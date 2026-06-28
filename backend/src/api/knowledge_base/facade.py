"""知识库子系统外观——封装所有 KB 组件的初始化与生命周期管理。

将 server.py 中 80 行的 _init_knowledge_base() 提取为可测试的外观类。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

logger = logging.getLogger(__name__)


class KnowledgeBaseFacade:
    """知识库子系统外观——一站式初始化。

    使用方式:
        facade = KnowledgeBaseFacade(settings)
        await facade.initialize(app)
    """

    def __init__(self, settings: Any) -> None:
        self._settings = settings
        self._vector_store: Any = None
        self._pipeline: Any = None
        self._scheduler: Any = None
        self._search_orchestrator: Any = None
        self._mediator: Any = None

    async def initialize(self, app: FastAPI) -> None:
        """初始化知识库子系统的所有组件并挂载到 app.state。"""
        from core.rag.vector_store import ChromaVectorStore, MilvusVectorStore
        from core.rag.vector_store_factory import VectorStoreFactory
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
        from api.knowledge_base.mediator import KnowledgeBaseMediator
        from api.knowledge_base.search_service import SearchOrchestrator, set_search_orchestrator
        from db.engine import async_session

        settings = self._settings

        # 嵌入模型
        embedding_model = get_embedding_model(
            model_name=settings.DEFAULT_EMBEDDING_MODEL,
            api_base=settings.DASHSCOPE_BASE_URL,
            api_key=settings.DASHSCOPE_API_KEY,
        )

        # 向量数据库 —— 工厂方法模式
        VectorStoreFactory.register("milvus", MilvusVectorStore)
        VectorStoreFactory.register("chroma", ChromaVectorStore)

        backend_kwargs: dict = {}
        if settings.VECTOR_DB_BACKEND == "milvus":
            backend_kwargs = {
                "uri": settings.MILVUS_URI,
                "user": settings.MILVUS_USER,
                "password": settings.MILVUS_PASSWORD,
                "db_name": settings.MILVUS_DEFAULT_DB,
            }
        elif settings.VECTOR_DB_BACKEND == "chroma":
            backend_kwargs = {
                "host": settings.CHROMA_HOST,
                "port": settings.CHROMA_PORT,
                "persist_dir": settings.CHROMA_PERSIST_DIR,
            }

        try:
            vector_store = VectorStoreFactory.create(settings.VECTOR_DB_BACKEND, **backend_kwargs)
            logger.info("向量数据库: %s", settings.VECTOR_DB_BACKEND)
        except ValueError:
            raise
        except Exception as e:
            logger.error("%s 初始化失败: %s", settings.VECTOR_DB_BACKEND, e)
            raise

        self._vector_store = vector_store
        app.state.vector_store = vector_store

        # 文档加载器注册表
        loader_registry = create_default_loader_registry()

        # 切片策略注册表
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
        pipeline.attach(DatabaseProgressObserver(async_session))
        pipeline.attach(LoggingProgressObserver())

        # 索引调度器（单例）
        scheduler = IndexingScheduler(
            pipeline=pipeline,
            max_concurrent=settings.INDEXING_MAX_CONCURRENT,
        )
        self._pipeline = pipeline
        self._scheduler = scheduler
        app.state.scheduler = scheduler
        logger.info("索引调度器已初始化 (max_concurrent=%d)", settings.INDEXING_MAX_CONCURRENT)

        # 知识库中介者
        mediator = KnowledgeBaseMediator(vector_store=vector_store)
        self._mediator = mediator
        app.state.kb_mediator = mediator
        logger.info("知识库中介者已初始化")

        # 检索编排器（策略模式：vector / bm25 / hybrid）
        search_orchestrator = SearchOrchestrator(
            vector_store=vector_store,
            embedding_model=embedding_model,
        )
        self._search_orchestrator = search_orchestrator
        app.state.search_orchestrator = search_orchestrator
        set_search_orchestrator(search_orchestrator)
        logger.info("检索编排器已初始化 (modes: %s)", search_orchestrator._registry.supported_modes)

    @property
    def vector_store(self) -> Any:
        return self._vector_store

    @property
    def scheduler(self) -> Any:
        return self._scheduler

    @property
    def mediator(self) -> Any:
        return self._mediator
