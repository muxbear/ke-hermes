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


def _init_knowledge_base(app: FastAPI) -> None:
    """初始化知识库向量存储和索引调度器，挂载到 app.state。"""
    from agent.config import settings
    from core.rag.vector_store import BaseVectorStore, MilvusVectorStore
    from core.rag.loaders import create_default_loader_registry
    from core.rag.splitters import create_chunk_registry
    from core.rag.embedding import get_embedding_model
    from api.knowledge_base.graph_service import GraphExtractionService
    from api.knowledge_base.doc_service import (
        DatabaseProgressObserver,
        IndexingPipeline,
        IndexingScheduler,
        LoggingProgressObserver,
    )

    kb_logger = logging.getLogger(__name__)

    # 嵌入模型（从环境变量配置读取）
    embedding_model = get_embedding_model(
        model_name=settings.DEFAULT_EMBEDDING_MODEL,
        api_base=settings.DASHSCOPE_BASE_URL,
        api_key=settings.DASHSCOPE_API_KEY,
    )

    # 向量数据库 —— 支持 milvus / chroma
    vector_store: BaseVectorStore | None = None
    if settings.VECTOR_DB_BACKEND == "milvus":
        try:
            vector_store = MilvusVectorStore(
                uri=settings.MILVUS_URI,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD,
                db_name=settings.MILVUS_DEFAULT_DB,
            )
            kb_logger.info("向量数据库: Milvus (%s, db=%s)",
                         settings.MILVUS_URI, settings.MILVUS_DEFAULT_DB)
        except Exception as e:
            kb_logger.error("Milvus 初始化失败: %s", e)
            raise
    elif settings.VECTOR_DB_BACKEND == "chroma":
        from core.rag.vector_store import ChromaVectorStore
        vector_store = ChromaVectorStore(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            persist_dir=settings.CHROMA_PERSIST_DIR,
        )
        kb_logger.info("向量数据库: Chroma (persist_dir=%s)", settings.CHROMA_PERSIST_DIR)
    else:
        raise RuntimeError(f"不支持的向量数据库后端: {settings.VECTOR_DB_BACKEND}")

    app.state.vector_store = vector_store

    # 文档加载器注册表
    loader_registry = create_default_loader_registry()

    # 切片策略注册表（语义策略需要嵌入模型）
    chunk_registry = create_chunk_registry({}, embedding_model=embedding_model)

    # 图谱抽取服务
    graph_service = GraphExtractionService()

    # 索引流水线
    pipeline = IndexingPipeline(
        loader_registry=loader_registry,
        chunk_registry=chunk_registry,
        embedding_model=embedding_model,
        vector_store=vector_store,
        graph_service=graph_service,
    )

    # 进度观察者
    from db.engine import async_session
    pipeline.attach(DatabaseProgressObserver(async_session))
    pipeline.attach(LoggingProgressObserver())

    # 索引调度器（单例）
    scheduler = IndexingScheduler(
        pipeline=pipeline,
        max_concurrent=settings.INDEXING_MAX_CONCURRENT,
    )
    app.state.scheduler = scheduler
    kb_logger.info(
        "索引调度器已初始化 (max_concurrent=%d)", settings.INDEXING_MAX_CONCURRENT
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    _init_knowledge_base(app)

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
