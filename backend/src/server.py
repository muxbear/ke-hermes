import asyncio
import logging
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    # uvicorn 在 Windows 上硬编码了 ProactorEventLoop，绕过了事件循环策略。
    # 通过 monkeypatch 修复以兼容 psycopg。
    import uvicorn.loops.asyncio as _uvicorn_loops

    _uvicorn_loops.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

load_dotenv()

from api import router
from api.deps import set_store
from core.store import create_store
from db.engine import init_db
from agent.graph import init_graph, shutdown_graph


async def _init_knowledge_base(app: FastAPI) -> None:
    """初始化知识库子系统——委托给 KnowledgeBaseFacade。"""
    from agent.config import settings
    from api.knowledge_base.facade import KnowledgeBaseFacade

    facade = KnowledgeBaseFacade(settings)
    await facade.initialize(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    await init_db()

    # 首次启动时种子化 MCP 工具和内置技能
    from api.mcp.service import seed_mcp_tools
    from api.skill.service import seed_builtin_skills
    from api.tools.service import seed_builtin_tools
    from db.engine import async_session

    async with async_session() as session:
        await seed_mcp_tools(session)
        await seed_builtin_skills(session)
        await seed_builtin_tools(session)
        await session.commit()

    # 迁移明文 api_key 为加密存储
    from api.providers.service import migrate_plaintext_api_keys
    async with async_session() as session:
        await migrate_plaintext_api_keys(session)
        await session.commit()

    await init_graph()
    store = await create_store()
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()

    # 初始化知识库子系统
    await _init_knowledge_base(app)

    yield
    await shutdown_graph()


app = FastAPI(
    title="ke-hermes",
    description="通用智能体服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
