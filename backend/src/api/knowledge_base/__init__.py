"""知识库模块。"""

from api.knowledge_base.kb_api import router as kb_router
from api.knowledge_base.doc_api import router as doc_router
from api.knowledge_base.graph_api import router as graph_router

__all__ = ["kb_router", "doc_router", "graph_router"]
