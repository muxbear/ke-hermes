"""Per-user sandbox manager with TTL, health checks, and cleanup."""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import timedelta

from opensandbox.models import NetworkPolicy, NetworkRule
from opensandbox.sync import SandboxSync

from agent.config import settings
from agent.sandbox.opensandbox_backend import OpenSandBoxBackend
from agent.sandbox.opensandbox_operate import _get_config_sync

logger = logging.getLogger(__name__)


@dataclass
class SandboxEntry:
    """Tracks a single user's sandbox and its lifecycle metadata."""

    sandbox: SandboxSync
    backend: OpenSandBoxBackend
    last_access: float
    user_id: str


class SandboxManager:
    """Manages per-user sandbox instances with TTL-based lifecycle.

    Thread-safe: all public methods are protected by an internal lock.

    Lifecycle:
      1. ``get_or_create_backend(user_id)`` checks the in-memory pool.
      2. If found: runs ``is_healthy()``; if unhealthy, kills and recreates.
      3. If healthy: calls ``sandbox.renew(timeout)`` to refresh the
         provider-side idle timeout, updates ``last_access``.
      4. If not found: creates a new sandbox via ``SandboxSync.create(...)``,
         wraps it in ``OpenSandBoxBackend``, and stores it.
      5. A background cleanup thread periodically kills sandboxes whose
         ``last_access`` exceeds ``ttl_seconds``.
    """

    def __init__(  # noqa: D107
        self,
        *,
        ttl_seconds: int | None = None,
        cleanup_interval: int | None = None,
        image: str | None = None,
        cpu: str | None = None,
        memory: str | None = None,
        idle_timeout_minutes: int | None = None,
    ) -> None:
        self._ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.SANDBOX_TTL_SECONDS
        self._cleanup_interval = (
            cleanup_interval if cleanup_interval is not None else settings.SANDBOX_CLEANUP_INTERVAL
        )
        self._image = image or settings.SANDBOX_IMAGE
        self._cpu = cpu or settings.SANDBOX_CPU
        self._memory = memory or settings.SANDBOX_MEMORY
        self._idle_timeout_minutes = (
            idle_timeout_minutes
            if idle_timeout_minutes is not None
            else settings.SANDBOX_IDLE_TIMEOUT_MINUTES
        )
        self._config = _get_config_sync()

        self._sandboxes: dict[str, SandboxEntry] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._cleanup_thread: threading.Thread | None = None

    # ---- Public API ----

    def get_or_create_backend(self, user_id: str) -> OpenSandBoxBackend:
        """Get or create a sandbox backend for the given user."""
        with self._lock:
            entry = self._sandboxes.get(user_id)
            if entry is not None:
                if self._is_healthy(entry.sandbox):
                    self._renew(entry)
                    entry.last_access = time.monotonic()
                    logger.debug("Reusing sandbox %s for user %s", entry.sandbox.id, user_id)
                    return entry.backend

                logger.warning(
                    "Sandbox %s for user %s is unhealthy, recreating",
                    entry.sandbox.id,
                    user_id,
                )
                self._kill_sandbox(entry.sandbox)
                del self._sandboxes[user_id]

            logger.info("Creating new sandbox for user %s", user_id)
            sandbox = self._create_sandbox()
            backend = OpenSandBoxBackend(sandbox=sandbox)
            self._sandboxes[user_id] = SandboxEntry(
                sandbox=sandbox,
                backend=backend,
                last_access=time.monotonic(),
                user_id=user_id,
            )
            return backend

    def start_cleanup(self) -> None:
        """Start the background cleanup thread (daemon, non-blocking)."""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            return
        self._stop_event.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="sandbox-cleanup",
            daemon=True,
        )
        self._cleanup_thread.start()
        logger.info("Sandbox cleanup thread started (interval=%ds)", self._cleanup_interval)

    def shutdown(self) -> None:
        """Stop cleanup loop and kill all tracked sandboxes."""
        self._stop_event.set()
        if self._cleanup_thread is not None:
            self._cleanup_thread.join(timeout=30)
        with self._lock:
            for entry in list(self._sandboxes.values()):
                self._kill_sandbox(entry.sandbox)
            self._sandboxes.clear()
        logger.info("SandboxManager shut down, all sandboxes killed")

    # ---- Internal helpers ----

    def _cleanup_loop(self) -> None:
        while not self._stop_event.wait(self._cleanup_interval):
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        now = time.monotonic()
        expired: list[str] = []
        with self._lock:
            for user_id, entry in self._sandboxes.items():
                if now - entry.last_access > self._ttl_seconds:
                    expired.append(user_id)
            for user_id in expired:
                entry = self._sandboxes.pop(user_id)
                logger.info(
                    "Sandbox %s for user %s expired (last access %.0fs ago)",
                    entry.sandbox.id,
                    user_id,
                    now - entry.last_access,
                )
                self._kill_sandbox(entry.sandbox)

    def _create_sandbox(self) -> SandboxSync:
        return SandboxSync.create(
            image=self._image,
            entrypoint=["/opt/opensandbox/code-interpreter.sh"],
            env={"PYTHON_VERSION": "3.11"},
            resource={"cpu": self._cpu, "memory": self._memory},
            timeout=timedelta(minutes=self._idle_timeout_minutes),
            connection_config=self._config,
            network_policy=NetworkPolicy(
                defaultAction="deny",
                egress=[
                    NetworkRule(action="allow", target="pypi.org"),
                    NetworkRule(action="allow", target="*.github.com"),
                    NetworkRule(action="allow", target="*.baidu.com"),
                ],
            ),
        )

    def _renew(self, entry: SandboxEntry) -> None:
        try:
            entry.sandbox.renew(timeout=timedelta(minutes=self._idle_timeout_minutes))
        except Exception:
            logger.warning(
                "Failed to renew sandbox %s for user %s",
                entry.sandbox.id,
                entry.user_id,
                exc_info=True,
            )

    @staticmethod
    def _is_healthy(sandbox: SandboxSync) -> bool:
        try:
            return sandbox.is_healthy()
        except Exception:
            logger.warning("Health check failed for sandbox %s", sandbox.id, exc_info=True)
            return False

    @staticmethod
    def _kill_sandbox(sandbox: SandboxSync) -> None:
        try:
            sandbox.kill()
        except Exception:
            logger.warning("Failed to kill sandbox %s", sandbox.id, exc_info=True)
