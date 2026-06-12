import asyncio
import logging
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    # uvicorn hardcodes ProactorEventLoop on Windows, bypassing the
    # event loop policy.  Monkeypatch it so psycopg can work.
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
    """Initialize KB vector store and indexing scheduler on app state."""
    from agent.config import settings
    from core.rag.vector_store import MilvusVectorStore, NoopVectorStore
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

    # Embedding model (from env config)
    embedding_model = get_embedding_model(
        model_name=settings.DEFAULT_EMBEDDING_MODEL,
        api_base=settings.DASHSCOPE_BASE_URL,
        api_key=settings.DASHSCOPE_API_KEY,
    )

    # Vector store — Milvus with fallback to Noop
    vector_store = None
    if settings.VECTOR_DB_BACKEND == "milvus":
        try:
            vector_store = MilvusVectorStore(
                uri=settings.MILVUS_URI,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD,
                db_name=settings.MILVUS_DEFAULT_DB,
            )
            kb_logger.info("Vector store: Milvus (%s, db=%s)",
                         settings.MILVUS_URI, settings.MILVUS_DEFAULT_DB)
        except Exception as e:
            kb_logger.error("Milvus init failed, falling back to NoopVectorStore: %s", e)
            vector_store = NoopVectorStore()
    else:
        vector_store = NoopVectorStore()
        kb_logger.info("Vector store: NoopVectorStore (VECTOR_DB_BACKEND=%s)",
                     settings.VECTOR_DB_BACKEND)

    app.state.vector_store = vector_store

    # Document loader registry
    loader_registry = create_default_loader_registry()

    # Chunk strategy registry (with embedding model for semantic strategy)
    chunk_registry = create_chunk_registry({}, embedding_model=embedding_model)

    # Graph extraction service
    graph_service = GraphExtractionService(backend=settings.GRAPH_STORE_BACKEND)

    # Pipeline
    pipeline = IndexingPipeline(
        loader_registry=loader_registry,
        chunk_registry=chunk_registry,
        embedding_model=embedding_model,
        vector_store=vector_store,
        graph_service=graph_service,
    )

    # Observers
    from db.engine import async_session
    pipeline.attach(DatabaseProgressObserver(async_session))
    pipeline.attach(LoggingProgressObserver())

    # Scheduler (singleton)
    scheduler = IndexingScheduler(
        pipeline=pipeline,
        max_concurrent=settings.INDEXING_MAX_CONCURRENT,
    )
    app.state.scheduler = scheduler
    kb_logger.info(
        "IndexingScheduler initialized (max_concurrent=%d)", settings.INDEXING_MAX_CONCURRENT
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Seed MCP tools and builtin skills on first run
    from api.mcp.service import seed_mcp_tools
    from api.skill.service import seed_builtin_skills
    from api.tools.service import seed_builtin_tools
    from db.engine import async_session

    async with async_session() as session:
        await seed_mcp_tools(session)
        await seed_builtin_skills(session)
        await seed_builtin_tools(session)
        await session.commit()

    # Migrate any plaintext api_key values to encrypted
    from api.providers.service import migrate_plaintext_api_keys
    async with async_session() as session:
        await migrate_plaintext_api_keys(session)
        await session.commit()

    await init_graph()
    store = await create_store()
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()

    # Initialize knowledge base subsystem
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
