"""User-aware sandbox backend that routes to per-user sandbox instances."""

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox
from langgraph.runtime import get_runtime

from agent.sandbox.opensandbox_backend import OpenSandBoxBackend
from agent.sandbox.sandbox_manager import SandboxManager


class UserAwareSandboxBackend(BaseSandbox):
    """Backend that routes sandbox operations to per-user sandboxes.

    At each method call, extracts the current ``user_id`` from the LangGraph
    runtime context via ``get_runtime()`` and delegates to the corresponding
    ``OpenSandBoxBackend`` managed by a ``SandboxManager``.

    Extends ``BaseSandbox`` so that all file operations (ls, read, write, edit,
    grep, glob) are inherited — they internally call ``self.execute()`` /
    ``self.upload_files()`` / ``self.download_files()`` with the user-specific
    backend.
    """

    def __init__(self, *, sandbox_manager: SandboxManager) -> None:  # noqa: D107
        self._manager = sandbox_manager

    def _get_user_backend(self) -> OpenSandBoxBackend:
        runtime = get_runtime()
        user_id: str = runtime.context.user_id
        return self._manager.get_or_create_backend(user_id)

    @property
    def id(self) -> str:  # noqa: D102
        return self._get_user_backend().id

    def execute(  # noqa: D102
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        backend = self._get_user_backend()
        return backend.execute(command, timeout=timeout)

    def upload_files(  # noqa: D102
        self,
        files: list[tuple[str, bytes]],
    ) -> list[FileUploadResponse]:
        backend = self._get_user_backend()
        return backend.upload_files(files)

    def download_files(  # noqa: D102
        self,
        paths: list[str],
    ) -> list[FileDownloadResponse]:
        backend = self._get_user_backend()
        return backend.download_files(paths)
