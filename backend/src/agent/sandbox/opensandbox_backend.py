from collections.abc import Callable
from time import time
from typing import cast
from uuid import uuid4

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox
from deepagents.graph import logger
from opensandbox.sync import SandboxSync

SyncPollingInterval = float | Callable[[float], float]
PollingStrategy = Callable[[float], float]


class OpenSandBoxBackend(BaseSandbox):
    """OpenSandBoxBackend 的实现符合 SandboxBackendProtocol协议.

    该实现继承了基类 BaseSandbox 的全部文件操作方法，仅基于开放沙箱（OpenSandbox）应用程序接口实现execute()方法。
    """

    def __init__(
        self,
        *,
        sandbox: SandboxSync,
        timeout: int = 30 * 60,
        sync_polling_interval: SyncPollingInterval = 0.1,
    ) -> None:
        """创建一个封装现有 OpenSandbox 的 SandboxBackend。

        Args:
            sandbox: 现有的 OpenSandbox 实例。
            timeout: 超时时间，单位为秒。
            sync_polling_interval: 同步轮询间隔，单位为秒。
        """
        self._sandbox = sandbox
        self._default_timeout = timeout
        polling_strategy: PollingStrategy
        if callable(sync_polling_interval):
            polling_strategy = cast("PollingStrategy", sync_polling_interval)
        else:

            def polling_strategy(_elapsed: float) -> float:
                return sync_polling_interval

        self._sync_polling_strategy = polling_strategy

    @property
    def sandbox(self) -> SandboxSync:
        """返回底层 SandboxSync 实例，用于高级操作（如网络策略修改）。"""
        return self._sandbox

    @property
    def id(self) -> str:
        """返回沙箱的唯一标识符。

        Returns:
            沙箱的唯一标识符。
        """
        return self._sandbox.id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """执行一个 Shell 命令并返回结果。

        Args:
            command: 要执行的 shell 命令字符串。
            timeout: 超时时间，单位为秒。

        Returns:
            ExecuteResponse: 执行命令的结果。
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        # return self._execute_via_session_logs(command, timeoout=effective_timeout)
        return self._execute_command(command, timeout=effective_timeout)

    def _execute_command(self, command: str, *, timeout: int) -> ExecuteResponse:
        """使用 OpenSandbox 的 API 执行命令

        Args:
            command: 要执行的 shell 命令字符串
            timeout: 超时时间，单位为秒
        """
        try:
            logger.debug(f"通过 OpenSandbox 的 API 执行命令：{command}")
            result = self._sandbox.commands.run(command)
            logger.debug(f"命令执行完成，执行结果码：{result.exit_code}")

            stdout = ""
            stderr = ""

            if result.logs.stdout:
                stdout = "\n".join([log.text for log in result.logs.stdout])
                logger.debug(f"命令标准输出长度：{len(stdout)}")

            if result.logs.stderr:
                stderr = "\n".join([log.text for log in result.logs.stderr])
                logger.debug(f"命令标准错误长度：{len(stderr)}")

            # 合并输出
            output = stdout
            if stderr and stderr.strip():
                output += f"\n<stderr>{stderr.strip()}</stderr>"

            logger.info(f"命令执行成功，退出码：{result.exit_code or 0}")

            return ExecuteResponse(
                output=output, exit_code=result.exit_code or 0, truncated=False
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"执行命令时发生错误：{error_msg}", exc_info=True)

            if "timeout" in error_msg.lower():
                logger.warning(f"命令在 {timeout} 秒后超时")
                return ExecuteResponse(
                    output=f"命令在 {timeout} 秒后超时", exit_code=124, truncated=False
                )

    def _execute_via_session_logs(
        self, command: str, *, timeout: int
    ) -> ExecuteResponse:
        """通过会话执行命令，并轮询日志直至执行完成。。

        Args:
            command: 要执行的 shell 命令字符串。
            timeout: 超时时间，单位为秒。

        Returns:
            ExecuteResponse: 执行命令的结果。
        """
        session_id = str(uuid4())
        self._sandbox.process.create_session(session_id)
        try:
            start_at = time.monotonic()
            result = self._sandbox.process.execute_session_command(
                session_id,
                # SessionExecuteRequest(command=command, run_async=True),
                timeout=timeout,
            )
        finally:
            self._sandbox.process.delete_session(session_id)

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """从 OpenSandbox 中下载文件

        Args:
            paths: 要下载文件的路径

            list: 下载结果列表
        """
        logger.info(f"开始下载 {len(paths)} 个文件: {paths}")
        responses: list[FileDownloadResponse] = []

        for i, path in enumerate(paths):
            logger.debug(f"正在下载第 {i + 1}/{len(paths)} 个文件: {path}")

            if not path.startswith("/"):
                logger.error("路径必须是绝对路径,以 / 开头")
                responses.append(
                    FileDownloadResponse(path=path, content=None, error="无效的路径")
                )
                continue

            try:
                logger.debug(f"正在从沙盒读取文件: {path}")
                content = self._sandbox.files.read_file(path)
                content_bytes = (
                    content.encode("utf-8") if isinstance(content, str) else content
                )
                logger.debug(f"文件读取成功，大小: {len(content_bytes)}")

                responses.append(
                    FileDownloadResponse(
                        path=path,
                        content=content_bytes,
                        error=None,
                    )
                )
            except Exception as e:
                logger.error(f"读取文件 {path} 时出错：{str(e)}")

                # 尝试检查文件是否存在
                try:
                    logger.debug(f"检查文件 {path} 是否存在")
                    result = self._sandbox.commands.run(
                        f"test -f '{path}' && echo 'exists'"
                    )
                    if (
                        not result.logs.stdout
                        or "exists" not in result.logs.stdout[0].text
                    ):
                        logger.error(f"文件 {path} 不存在")
                        responses.append(
                            FileDownloadResponse(
                                path=path, content=None, error="file_not_found"
                            )
                        )
                    else:
                        logger.error(f"文件 {path} 存在，但读取失败，错误：{str(e)}")
                        responses.append(
                            path=path, content=None, error=f"read_error: {str(e)}"
                        )
                except Exception as check_error:
                    logger.error(
                        f"检查文件 {path} 时出错：{check_error}", exc_info=True
                    )
                    responses.append(
                        FileDownloadResponse(
                            path=path,
                            content=None,
                            error=f"check_error: {str(check_error)}",
                        )
                    )

        success_count = sum(1 for r in responses if r.error is None)
        logger.info(f"文件下载完成，成功下载 {success_count} 个文件")
        return responses

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """上传文件到 OpenSandbox

        Args:
            files: 要上传的文件列表

            list: 已经上传的文件列表
        """
        from opensandbox.models import WriteEntry

        logger.info(f"准备上传 {len(files)} 个文件")
        responses: list[FileUploadResponse] = []
        upload_entries = []

        for i, (path, content) in enumerate(files):
            logger.debug(
                f"正在上传第 {i}/{len(files)} 文件：{path}, 大小：{len(content)} 字节"
            )
            if not path.startswith("/"):
                responses.append(FileUploadResponse(path=path, error="invalid_path"))
                continue

            try:
                # 将字节内容转换成字符串
                if isinstance(content, bytes):
                    try:
                        content_str = content.decode("utf-8")
                        logger.debug(
                            f"用 utf-8 解码字节，获取到内容长度：{len(content_str)}"
                        )
                    except UnicodeDecodeError as decode_error:
                        logger.warning(
                            f"用 utf-8 解码失败，将以字符串的形式存储，错误信息: {decode_error}"
                        )
                        content_str = str(content)
                else:
                    content_str = str(content)

                upload_entries.append(
                    WriteEntry(path=path, data=content_str, mode=0o644)
                )
                responses.append(FileUploadResponse(path=path, error=None))
                logger.debug(f"文件 {path} 已加入到上传队列")
            except Exception as e:
                logger.error(f"准备上传文件 {path} 出错：{str(e)}", exc_info=True)
                responses.append(FileUploadResponse(path=path, error=str(e)))

            # 如果有文件需要上传
            if upload_entries:
                logger.info(f"正在向沙盒上传文件，总共 {len(upload_entries)} 个文件")
                try:
                    self._sandbox.files.write_files(upload_entries)
                    logger.info(f"成功上传 {len(upload_entries)} 个文件")
                except Exception as e:
                    logger.error("上传文件时出错：str(e)", exc_info=True)

                    # 发生错误时，更新响应
                    for i, resp in enumerate(responses):
                        if resp.error is None:
                            responses[i] = FileUploadResponse(
                                path=resp.path, error=f"upload_failed：{str(e)}"
                            )
                        else:
                            logger.warning("没有有效的文件需要上传")

            # 上传结果
            success_count = sum(1 for r in responses if r.error is None)
            error_count = len(responses) - success_count
            return responses
