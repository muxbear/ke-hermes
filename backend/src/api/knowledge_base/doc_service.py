"""文档管理 & 索引流水线服务——模板方法 + 观察者 + 单例模式。"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from agent.config import settings
from api.knowledge_base.doc_state import IndexingContext, DocState, QueuedState
from api.knowledge_base.schemas import KBDocResponse, KBDocUploadResponse, DocStageInfo
from core.rag.loaders import DocumentLoaderRegistry, create_default_loader_registry
from core.rag.splitters import ChunkStrategyRegistry, create_chunk_registry
from core.rag.vector_store import BaseVectorStore
from db.models.knowledge_base import KnowledgeBase
from db.models.knowledge_base_document import KnowledgeBaseDocument

logger = logging.getLogger(__name__)

# 各阶段的预估进度基线
STAGE_PROGRESS = {"queued": 0, "parsing": 15, "chunking": 30, "embedding": 55,
                  "bm25": 70, "extracting": 85, "indexed": 100}
STAGE_NAMES = ["排队", "解析", "切片", "向量化", "BM25 倒排", "实体抽取", "关系抽取", "入库"]

ALLOWED_EXTENSIONS = {
    "pdf", "docx", "xlsx", "pptx", "csv", "json", "md", "html", "txt",
    "png", "jpg", "jpeg",
}
MAX_FILE_SIZE_MB = 100


def _format_bytes(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    s: float = size_bytes
    for unit in ["KB", "MB", "GB", "TB"]:
        s /= 1024
        if s < 1024:
            return f"{s:.1f} {unit}"
    return f"{s:.1f} PB"


def _get_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext if ext in ALLOWED_EXTENSIONS else "unknown"


def compute_stages(status: str, error_message: str | None = None) -> list[dict]:
    """根据状态计算 8 阶段状态。"""
    status_order = ["queued", "parsing", "chunking", "embedding", "bm25", "extracting", "indexed"]
    stages = []
    current_idx = status_order.index(status) if status in status_order else -1

    for i, name in enumerate(STAGE_NAMES):
        if i < current_idx:
            stages.append({"name": name, "status": "done", "pct": 100})
        elif i == current_idx:
            stages.append({"name": name, "status": "running", "pct": STAGE_PROGRESS.get(status, 50)})
        else:
            stages.append({"name": name, "status": "pending", "pct": 0})

    if status == "failed":
        failed_idx = _infer_failed_stage_index(error_message)
        if failed_idx < len(stages):
            stages[failed_idx]["status"] = "failed"
            # 将失败阶段之前的阶段标记为完成（失败前已成功执行）
            for j in range(failed_idx):
                stages[j]["status"] = "done"
                stages[j]["pct"] = 100

    return stages


def _infer_failed_stage_index(error_message: str | None) -> int:
    """从错误信息中推断失败阶段索引。

    映射关系（错误消息关键词 → STAGE_NAMES 索引）：
    - "解析" → 1
    - "切片" → 2
    - "向量化" → 3
    - "BM25" → 4
    - "实体" → 5
    - "关系" → 6
    """
    if not error_message:
        return 1  # 兜底：无法推断时默认解析阶段
    msg = error_message
    if "向量化" in msg:
        return 3
    if "切片" in msg:
        return 2
    if "BM25" in msg:
        return 4
    if "实体" in msg:
        return 5
    if "关系" in msg:
        return 6
    if "解析" in msg:
        return 1
    return 1  # 兜底


# ══════════════════════════════════════════════════════════════
# 观察者模式
# ══════════════════════════════════════════════════════════════

class ProgressObserver(ABC):
    """索引进度观察者抽象接口。"""

    @abstractmethod
    async def on_progress(self, ctx: IndexingContext) -> None:
        ...


class DatabaseProgressObserver(ProgressObserver):
    """数据库进度观察者——将进度写入 knowledge_base_documents 表。"""

    def __init__(self, db_session_factory):
        self._db_factory = db_session_factory

    async def on_progress(self, ctx: IndexingContext) -> None:
        try:
            async with self._db_factory() as db:
                stmt = (
                    update(KnowledgeBaseDocument)
                    .where(KnowledgeBaseDocument.id == ctx.doc_id)
                    .values(
                        status=ctx.status,
                        progress=ctx.progress,
                        error_message=ctx.error_message,
                        chunks_count=len(ctx.chunks),
                        indexed_at=datetime.utcnow() if ctx.status == "indexed" else None,
                    )
                )
                await db.execute(stmt)
                await db.commit()
        except Exception as e:
            logger.error("DatabaseProgressObserver 写入失败: %s", e)


class LoggingProgressObserver(ProgressObserver):
    """日志进度观察者。"""

    async def on_progress(self, ctx: IndexingContext) -> None:
        stage = ctx.current_state.name if ctx.current_state else "unknown"
        logger.info("文档 %s: 状态=%s 进度=%d%% 阶段=%s", ctx.doc_id, ctx.status, ctx.progress, stage)


# ══════════════════════════════════════════════════════════════
# 模板方法模式——IndexingPipeline
# ══════════════════════════════════════════════════════════════

class IndexingPipeline:
    """索引流水线——模板方法模式定义 8 阶段骨架。"""

    def __init__(
        self,
        loader_registry: DocumentLoaderRegistry,
        chunk_registry: ChunkStrategyRegistry,
        embedding_model,
        vector_store: BaseVectorStore,
        graph_service,
    ):
        self.loader_registry = loader_registry
        self.chunk_registry = chunk_registry
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.graph_service = graph_service
        self._observers: list[ProgressObserver] = []

    def attach(self, observer: ProgressObserver) -> None:
        self._observers.append(observer)

    async def _notify(self, ctx: IndexingContext) -> None:
        for observer in self._observers:
            try:
                await observer.on_progress(ctx)
            except Exception as e:
                logger.error("观察者 %s 执行失败: %s", type(observer).__name__, e)

    async def execute(self, task: IndexingTask) -> None:
        """模板方法：定义 8 阶段索引骨架。"""
        ctx = IndexingContext(
            doc_id=task.doc_id,
            kb_id=task.kb_id,
            file_path=task.file_path,
            file_type=task.file_type,
            config=task.config,
            current_state=QueuedState(),
            status="queued",
            progress=0,
        )

        async def _on_status_change(c: IndexingContext) -> None:
            await self._notify(c)
        ctx.on_status_change = _on_status_change

        await self._notify(ctx)
        try:
            await self._run_state_machine(ctx)
        except Exception as e:
            logger.exception("流水线处理文档 %s 失败", task.doc_id)
            await ctx.fail(str(e))
            await self._notify(ctx)

    async def _run_state_machine(self, ctx: IndexingContext) -> None:
        """驱动状态机直到终态。"""
        while ctx.current_state is not None:
            state = ctx.current_state
            await state.handle(ctx, self)
            if ctx.status in ("indexed", "failed"):
                break


# ══════════════════════════════════════════════════════════════
# 调度器——单例模式
# ══════════════════════════════════════════════════════════════

@dataclass
class IndexingTask:
    kb_id: str
    doc_id: str
    file_path: str
    file_type: str
    config: dict


class IndexingScheduler:
    """索引任务调度器（单例）。"""

    _instance: IndexingScheduler | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        pipeline: IndexingPipeline | None = None,
        max_concurrent: int = 3,
    ):
        if self._initialized:
            return
        self._initialized = True
        self._pipeline = pipeline
        self._queue: deque[IndexingTask] = deque()
        self._running: dict[str, asyncio.Task] = {}
        self._max_concurrent = max_concurrent

    @classmethod
    def instance(cls) -> IndexingScheduler | None:
        return cls._instance

    async def enqueue(self, task: IndexingTask) -> None:
        self._queue.append(task)
        logger.info("任务已入队: 文档=%s, 队列长度=%d", task.doc_id, len(self._queue))
        await self._try_start_next()

    async def _try_start_next(self) -> None:
        if not self._queue or len(self._running) >= self._max_concurrent:
            return
        task = self._queue.popleft()
        async_task = asyncio.create_task(self._pipeline.execute(task))  # type: ignore[union-attr]
        self._running[task.doc_id] = async_task
        async_task.add_done_callback(lambda _: self._on_task_done(task.doc_id))

    def _on_task_done(self, doc_id: str) -> None:
        self._running.pop(doc_id, None)
        if self._queue:
            asyncio.create_task(self._try_start_next())


# ══════════════════════════════════════════════════════════════
# 文档业务逻辑
# ══════════════════════════════════════════════════════════════

async def upload_documents(
    db: AsyncSession,
    kb_id: str,
    user_id: str,
    files: list[UploadFile],
    scheduler: IndexingScheduler | None = None,
) -> list[KBDocUploadResponse]:
    """上传文档并触发索引流水线。"""
    # 校验知识库
    kb = (
        await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    upload_dir = os.path.join(settings.doc_upload_dir, kb_id)
    os.makedirs(upload_dir, exist_ok=True)

    results: list[KBDocUploadResponse] = []
    total_new_bytes = 0

    for file in files:
        # 校验文件名
        filename = file.filename or "unknown"
        file_type = _get_file_type(filename)
        if file_type == "unknown":
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {filename}")

        # 读取并校验大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"文件 {filename} 超过最大大小 {MAX_FILE_SIZE_MB}MB",
            )

        doc_id = str(uuid.uuid4())
        storage_dir = os.path.join(upload_dir, doc_id)
        os.makedirs(storage_dir, exist_ok=True)
        storage_path = os.path.join(storage_dir, filename)

        with open(storage_path, "wb") as f:
            f.write(content)

        now = datetime.utcnow()
        doc = KnowledgeBaseDocument(
            id=doc_id,
            kb_id=kb_id,
            name=filename,
            type=file_type,
            size_bytes=len(content),
            storage_path=storage_path,
            status="queued",
            uploaded_at=now,
        )
        db.add(doc)
        total_new_bytes += len(content)

        results.append(KBDocUploadResponse(
            id=doc_id, name=filename, type=file_type,
            size_display=_format_bytes(len(content)),
            status="queued", uploaded_at=now,
        ))

        # 入队索引任务
        if scheduler:
            await scheduler.enqueue(IndexingTask(
                kb_id=kb_id, doc_id=doc_id, file_path=storage_path,
                file_type=file_type, config=kb.config,
            ))

    # 更新知识库统计
    kb.docs_count = (kb.docs_count or 0) + len(files)
    kb.size_bytes = (kb.size_bytes or 0) + total_new_bytes
    if kb.status == "draft":
        kb.status = "indexing"
    kb.updated_at = datetime.utcnow()

    return results


async def list_documents(
    db: AsyncSession,
    kb_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
) -> dict:
    """获取文档列表（分页 + 筛选）。"""
    from api.knowledge_base.service import _get_kb_or_404
    await _get_kb_or_404(db, kb_id, user_id)

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    conditions = [KnowledgeBaseDocument.kb_id == kb_id]
    if search:
        conditions.append(KnowledgeBaseDocument.name.ilike(f"%{search}%"))
    if status:
        conditions.append(KnowledgeBaseDocument.status == status)

    total = (
        await db.execute(
            select(func.count()).select_from(KnowledgeBaseDocument).where(*conditions)
        )
    ).scalar() or 0

    rows = (
        await db.execute(
            select(KnowledgeBaseDocument)
            .where(*conditions)
            .order_by(KnowledgeBaseDocument.uploaded_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()

    items = []
    for r in rows:
        items.append(KBDocResponse(
            id=r.id, name=r.name, type=r.type,
            size_display=_format_bytes(r.size_bytes or 0),
            status=r.status, progress=r.progress or 0,
            chunks_count=r.chunks_count or 0,
            entities_count=r.entities_count or 0,
            relations_count=r.relations_count or 0,
            uploaded_at=r.uploaded_at,
            indexed_at=r.indexed_at,
            error_message=r.error_message,
            stages=[DocStageInfo(**s) for s in compute_stages(r.status or "queued", r.error_message)],
        ))

    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_document(
    db: AsyncSession, kb_id: str, doc_id: str, user_id: str,
) -> KBDocResponse:
    """获取文档详情（含流水线状态）。"""
    from api.knowledge_base.service import _get_kb_or_404
    await _get_kb_or_404(db, kb_id, user_id)

    doc = (
        await db.execute(
            select(KnowledgeBaseDocument).where(
                KnowledgeBaseDocument.id == doc_id,
                KnowledgeBaseDocument.kb_id == kb_id,
            )
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    return KBDocResponse(
        id=doc.id, name=doc.name, type=doc.type,
        size_display=_format_bytes(doc.size_bytes or 0),
        status=doc.status, progress=doc.progress or 0,
        chunks_count=doc.chunks_count or 0,
        entities_count=doc.entities_count or 0,
        relations_count=doc.relations_count or 0,
        uploaded_at=doc.uploaded_at,
        indexed_at=doc.indexed_at,
        error_message=doc.error_message,
        stages=[DocStageInfo(**s) for s in compute_stages(doc.status or "queued", doc.error_message)],
    )


async def delete_document(
    db: AsyncSession, kb_id: str, doc_id: str, user_id: str,
    vector_store: BaseVectorStore | None = None,
) -> None:
    """删除文档——级联删除向量数据和源文件。"""
    from api.knowledge_base.service import _get_kb_or_404
    await _get_kb_or_404(db, kb_id, user_id)

    doc = (
        await db.execute(
            select(KnowledgeBaseDocument).where(
                KnowledgeBaseDocument.id == doc_id,
                KnowledgeBaseDocument.kb_id == kb_id,
            )
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 从向量数据库删除
    if vector_store:
        try:
            await vector_store.delete_by_doc_id(kb_id, doc_id)
        except Exception as e:
            logger.error("删除文档 %s 向量数据失败: %s", doc_id, e)

    # 删除源文件
    storage_dir = os.path.dirname(doc.storage_path)
    if os.path.isdir(storage_dir):
        shutil.rmtree(storage_dir, ignore_errors=True)

    # 更新知识库统计
    kb = (
        await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
    ).scalar_one_or_none()
    if kb:
        kb.docs_count = max(0, (kb.docs_count or 0) - 1)
        kb.size_bytes = max(0, (kb.size_bytes or 0) - (doc.size_bytes or 0))
        kb.updated_at = datetime.utcnow()

    await db.delete(doc)


async def retry_document(
    db: AsyncSession, kb_id: str, doc_id: str, user_id: str,
    scheduler: IndexingScheduler | None = None,
) -> KBDocResponse:
    """重试失败文档的索引。"""
    from api.knowledge_base.service import _get_kb_or_404
    await _get_kb_or_404(db, kb_id, user_id)

    doc = (
        await db.execute(
            select(KnowledgeBaseDocument).where(
                KnowledgeBaseDocument.id == doc_id,
                KnowledgeBaseDocument.kb_id == kb_id,
            )
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.status != "failed":
        raise HTTPException(status_code=400, detail="只能重试失败的文档")

    doc.status = "queued"
    doc.progress = 0
    doc.error_message = None

    kb = (
        await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
    ).scalar_one_or_none()

    if scheduler and kb:
        await scheduler.enqueue(IndexingTask(
            kb_id=kb_id, doc_id=doc_id, file_path=doc.storage_path,
            file_type=doc.type, config=kb.config,
        ))

    return KBDocResponse(
        id=doc.id, name=doc.name, type=doc.type,
        size_display=_format_bytes(doc.size_bytes or 0),
        status=doc.status, progress=doc.progress,
        chunks_count=doc.chunks_count or 0,
        entities_count=doc.entities_count or 0,
        relations_count=doc.relations_count or 0,
        uploaded_at=doc.uploaded_at,
        indexed_at=doc.indexed_at,
        error_message=doc.error_message,
        stages=[],
    )
