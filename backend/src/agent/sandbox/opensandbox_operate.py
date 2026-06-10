import asyncio
import os
from datetime import timedelta

from agent.config import settings
import httpx
from deepagents.graph import logger

from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig, ConnectionConfigSync
from opensandbox.models import NetworkPolicy, NetworkRule, WriteEntry

from opensandbox.sync import SandboxSync

from code_interpreter import CodeInterpreter, SupportedLanguage


def _default_network_policy(
    extra_domains: list[str] | None = None,
) -> NetworkPolicy:
    """构建沙盒网络策略，合并默认域名和额外域名。"""
    rules = [
        NetworkRule(action="allow", target="pypi.org"),
        NetworkRule(action="allow", target="*.github.com"),
        NetworkRule(action="allow", target="*.baidu.com"),
    ]
    for domain in extra_domains or []:
        rules.append(NetworkRule(action="allow", target=domain))
    return NetworkPolicy(defaultAction="deny", egress=rules)


def create_sandboxsync(config=None, sandbox_id=None, image=None):
    """获取或创建 SandboxSync

    Args:
        config: ConnectionConfigSync
        sandbox_id: 可选，要连接的沙盒标识
        image: 可选，创建沙盒时使用的镜像
    """
    if not config:
        config = _get_config_sync()

    if sandbox_id:
        try:
            sandbox = SandboxSync.connect(
                sandbox_id=sandbox_id, connection_config=config
            )
            return sandbox
        except Exception as e:
            logger.error(f"连接到沙盒 {sandbox_id} 出错：{str(e)}")
            raise

    if not image:
        image = "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.0.2"

    sandbox = SandboxSync.create(
        image=image,
        entrypoint=["/opt/opensandbox/code-interpreter.sh"],
        env={"PYTHON_VERSION": "3.11"},
        resource={"cpu": "2", "memory": "3Gi"},
        timeout=timedelta(minutes=10),  # 10 分钟不使用会停止沙盒
        connection_config=config,
        network_policy=_default_network_policy(),
    )

    return sandbox


async def create_sandbox(config=None, sandbox_id=None, image=None):
    """获取或创建 Sandbox

    Args:
        config: ConnectionConfig
        sandbox_id: 可选，要连接的沙盒标识
        image: 可选，创建沙盒时使用的镜像
    """
    if not config:
        config = _get_config()

    if sandbox_id:
        try:
            sandbox = await Sandbox.connect(
                sandbox_id=sandbox_id, connection_config=config
            )
            return sandbox
        except Exception as e:
            logger.error(f"连接到沙盒 {sandbox_id} 出错：{str(e)}")
            raise

    if not image:
        image = "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.0.2"

    sandbox = await Sandbox.create(
        image=image,
        entrypoint=["/opt/opensandbox/code-interpreter.sh"],
        env={"PYTHON_VERSION": "3.11"},
        resource={"cpu": "2", "memory": "3Gi"},
        timeout=timedelta(minutes=10),
        connection_config=config,
        network_policy=_default_network_policy(),
    )

    return sandbox


def list_running_sandbox(config):
    """列出所有正在运行的沙盒"""
    raise NotImplementedError("list_running_sandbox 尚未实现")


def _get_config_sync():
    """获取沙盒连接配置，优先从环境变量读取。"""
    domain = settings.OPENSANDBOX_DOMAIN
    api_key = settings.OPENSANDBOX_API_KEY
    return ConnectionConfigSync(
        domain=domain,
        api_key=api_key,
        use_server_proxy=True,
        request_timeout=timedelta(seconds=60),
        transport=httpx.HTTPTransport(limits=httpx.Limits(max_connections=20)),
    )


def _get_config():
    """获取沙盒连接配置，优先从环境变量读取。"""
    domain = settings.OPENSANDBOX_DOMAIN
    api_key = settings.OPENSANDBOX_API_KEY
    return ConnectionConfig(
        domain=domain,
        api_key=api_key,
        use_server_proxy=True,
        request_timeout=timedelta(seconds=60),
        transport=httpx.HTTPTransport(limits=httpx.Limits(max_connections=20)),
    )


def main():
    config = _get_config_sync()
    sandbox = create_sandboxsync(config)


async def main():
    config = _get_config()
    sandbox = await create_sandbox(config)

    async with sandbox:
        # 2. Execute a shell command
        execution = await sandbox.commands.run("echo 'Hello OpenSandbox!'")
        print(execution.logs.stdout[0].text)

        # 3. Write a file
        await sandbox.files.write_files(
            [
                WriteEntry(path="/tmp/hello.txt", data="Hello World", mode=644),
            ]
        )

        # 4. Read a file
        content = await sandbox.files.read_file("/tmp/hello.txt")
        print(f"Content: {content}")

        # 5. Create a code interpreter
        interpreter = await CodeInterpreter.create(sandbox)

        # 6. 执行 Python 代码
        result = await interpreter.codes.run(
            """
                import sys
                print(sys.version)
                result = 2 + 2
                result
            """,
            language=SupportedLanguage.PYTHON,
        )

        print(result.result[0].text)
        print(result.logs.stdout[0].text)

    # 7. Cleanup the sandbox
    await sandbox.kill()


if __name__ == "__main__":
    main()
    # asyncio.run(main())
