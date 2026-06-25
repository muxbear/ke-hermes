from dataclasses import dataclass


@dataclass
class Context:
    """Agent 运行时上下文。

    Attributes:
        server_info: 服务端标识。
        user_id: 当前用户 ID（来自 JWT）。
        org_id: 当前用户所属组织 ID，用于组织级只读记忆隔离；单租户默认 "default-org"。
    """

    server_info: str
    user_id: str
    org_id: str = "default-org"
