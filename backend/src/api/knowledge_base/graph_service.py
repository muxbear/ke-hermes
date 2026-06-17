"""知识图谱服务——基于 LangExtract 的实体/关系抽取 & 查询."""

import asyncio
import logging
import os
import textwrap
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.knowledge_base_entity import KnowledgeBaseEntity
from db.models.knowledge_base_relation import KnowledgeBaseRelation

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = textwrap.dedent("""\
    从文本中提取实体和实体之间的关系。仅提取文本中明确出现的实体和关系，不要虚构。

    实体类型必须是以下之一: 人物、组织、产品、技术、概念、算法、模型、框架、数据集、地点、时间、事件。
    每个 entity 的 extraction_text 必须是原文中出现的精确文本片段，不得改写。
    每个 entity 的 attributes 中必须包含 type 字段，写明实体类型。

    每个 relation 的 extraction_text 应为描述两个实体关系的原文片段。
    每个 relation 的 attributes 中必须包含:
      - from: 关系起始实体（必须与某个已提取 entity 的 extraction_text 完全一致）
      - to: 关系目标实体（必须与某个已提取 entity 的 extraction_text 完全一致）
      - label: 关系标签（如"开发"、"使用"、"基于"、"包含"、"发布于"、"隶属于"等）

    from 和 to 的值必须与对应 entity 的 extraction_text 精确匹配，包括标点和空格。""")

_EXTRACTION_EXAMPLES = [
    # 示例 1：企业/人物场景
    {
        "text": (
            "2024年3月，张明加入阿里巴巴达摩院，担任NLP研究科学家。"
            "他主导开发了大规模语言模型「通义千问」，该模型在多项基准测试中表现优异。"
            "阿里巴巴总部位于杭州，由马云于1999年创立。"
        ),
        "extractions": [
            {"extraction_class": "entity", "extraction_text": "张明", "attributes": {"type": "人物"}},
            {"extraction_class": "entity", "extraction_text": "阿里巴巴达摩院", "attributes": {"type": "组织"}},
            {"extraction_class": "entity", "extraction_text": "NLP研究科学家", "attributes": {"type": "概念"}},
            {"extraction_class": "entity", "extraction_text": "通义千问", "attributes": {"type": "产品"}},
            {"extraction_class": "entity", "extraction_text": "大规模语言模型", "attributes": {"type": "概念"}},
            {"extraction_class": "entity", "extraction_text": "杭州", "attributes": {"type": "地点"}},
            {"extraction_class": "entity", "extraction_text": "马云", "attributes": {"type": "人物"}},
            {"extraction_class": "entity", "extraction_text": "1999年", "attributes": {"type": "时间"}},
            {"extraction_class": "entity", "extraction_text": "2024年3月", "attributes": {"type": "时间"}},
            {"extraction_class": "relation", "extraction_text": "张明加入阿里巴巴达摩院", "attributes": {"from": "张明", "to": "阿里巴巴达摩院", "label": "任职于"}},
            {"extraction_class": "relation", "extraction_text": "张明主导开发通义千问", "attributes": {"from": "张明", "to": "通义千问", "label": "开发"}},
            {"extraction_class": "relation", "extraction_text": "阿里巴巴总部位于杭州", "attributes": {"from": "阿里巴巴达摩院", "to": "杭州", "label": "位于"}},
            {"extraction_class": "relation", "extraction_text": "马云创立阿里巴巴", "attributes": {"from": "马云", "to": "阿里巴巴达摩院", "label": "创立"}},
        ],
    },
    # 示例 2：AI/技术文档场景
    {
        "text": (
            "Transformer 架构由 Vaswani 等人在 2017 年的论文《Attention Is All You Need》中提出。"
            "该架构完全基于自注意力机制（Self-Attention），摒弃了传统的 RNN 和 CNN 结构。"
            "BERT 模型由 Google 在 2018 年发布，采用 Transformer 的编码器部分进行预训练。"
            "随后 OpenAI 推出了 GPT 系列模型，使用 Transformer 的解码器部分，"
            "在文本生成任务上取得了突破性进展。HuggingFace 提供了 Transformers 开源库，"
            "支持 PyTorch 和 TensorFlow 两大深度学习框架。"
        ),
        "extractions": [
            {"extraction_class": "entity", "extraction_text": "Transformer", "attributes": {"type": "模型"}},
            {"extraction_class": "entity", "extraction_text": "Vaswani", "attributes": {"type": "人物"}},
            {"extraction_class": "entity", "extraction_text": "Self-Attention", "attributes": {"type": "算法"}},
            {"extraction_class": "entity", "extraction_text": "BERT", "attributes": {"type": "模型"}},
            {"extraction_class": "entity", "extraction_text": "Google", "attributes": {"type": "组织"}},
            {"extraction_class": "entity", "extraction_text": "GPT", "attributes": {"type": "模型"}},
            {"extraction_class": "entity", "extraction_text": "OpenAI", "attributes": {"type": "组织"}},
            {"extraction_class": "entity", "extraction_text": "HuggingFace", "attributes": {"type": "组织"}},
            {"extraction_class": "entity", "extraction_text": "Transformers", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "PyTorch", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "TensorFlow", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "2017 年", "attributes": {"type": "时间"}},
            {"extraction_class": "entity", "extraction_text": "2018 年", "attributes": {"type": "时间"}},
            {"extraction_class": "relation", "extraction_text": "Vaswani 等人提出 Transformer 架构", "attributes": {"from": "Vaswani", "to": "Transformer", "label": "提出"}},
            {"extraction_class": "relation", "extraction_text": "Transformer 基于 Self-Attention", "attributes": {"from": "Transformer", "to": "Self-Attention", "label": "基于"}},
            {"extraction_class": "relation", "extraction_text": "BERT 使用 Transformer 编码器", "attributes": {"from": "BERT", "to": "Transformer", "label": "基于"}},
            {"extraction_class": "relation", "extraction_text": "Google 发布 BERT", "attributes": {"from": "Google", "to": "BERT", "label": "发布"}},
            {"extraction_class": "relation", "extraction_text": "OpenAI 推出 GPT", "attributes": {"from": "OpenAI", "to": "GPT", "label": "开发"}},
            {"extraction_class": "relation", "extraction_text": "GPT 使用 Transformer 解码器", "attributes": {"from": "GPT", "to": "Transformer", "label": "基于"}},
            {"extraction_class": "relation", "extraction_text": "HuggingFace 提供 Transformers", "attributes": {"from": "HuggingFace", "to": "Transformers", "label": "开发"}},
            {"extraction_class": "relation", "extraction_text": "Transformers 支持 PyTorch", "attributes": {"from": "Transformers", "to": "PyTorch", "label": "支持"}},
            {"extraction_class": "relation", "extraction_text": "Transformers 支持 TensorFlow", "attributes": {"from": "Transformers", "to": "TensorFlow", "label": "支持"}},
        ],
    },
    # 示例 3：RAG/知识库系统场景
    {
        "text": (
            "RAG（Retrieval-Augmented Generation）系统由检索器和生成器两部分组成。"
            "检索器通常基于向量数据库（如 Milvus 或 Chroma）实现，使用 Embedding 模型"
            "将文档转换为向量进行相似度搜索。LangChain 和 LlamaIndex 是两个主流的 "
            "RAG 开发框架。本文介绍的 Ke-Hermes 系统采用 FastAPI 作为 Web 框架，"
            "使用 DeepSeek 作为大语言模型，DashScope 提供 Embedding 服务，"
            "LangExtract 负责知识图谱的实体关系抽取。"
        ),
        "extractions": [
            {"extraction_class": "entity", "extraction_text": "RAG", "attributes": {"type": "技术"}},
            {"extraction_class": "entity", "extraction_text": "Milvus", "attributes": {"type": "产品"}},
            {"extraction_class": "entity", "extraction_text": "Chroma", "attributes": {"type": "产品"}},
            {"extraction_class": "entity", "extraction_text": "Embedding", "attributes": {"type": "技术"}},
            {"extraction_class": "entity", "extraction_text": "LangChain", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "LlamaIndex", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "Ke-Hermes", "attributes": {"type": "产品"}},
            {"extraction_class": "entity", "extraction_text": "FastAPI", "attributes": {"type": "框架"}},
            {"extraction_class": "entity", "extraction_text": "DeepSeek", "attributes": {"type": "模型"}},
            {"extraction_class": "entity", "extraction_text": "DashScope", "attributes": {"type": "产品"}},
            {"extraction_class": "entity", "extraction_text": "LangExtract", "attributes": {"type": "框架"}},
            {"extraction_class": "relation", "extraction_text": "RAG 基于 Milvus", "attributes": {"from": "RAG", "to": "Milvus", "label": "使用"}},
            {"extraction_class": "relation", "extraction_text": "RAG 基于 Chroma", "attributes": {"from": "RAG", "to": "Chroma", "label": "使用"}},
            {"extraction_class": "relation", "extraction_text": "RAG 使用 Embedding", "attributes": {"from": "RAG", "to": "Embedding", "label": "使用"}},
            {"extraction_class": "relation", "extraction_text": "Ke-Hermes 采用 FastAPI", "attributes": {"from": "Ke-Hermes", "to": "FastAPI", "label": "基于"}},
            {"extraction_class": "relation", "extraction_text": "Ke-Hermes 使用 DeepSeek", "attributes": {"from": "Ke-Hermes", "to": "DeepSeek", "label": "使用"}},
            {"extraction_class": "relation", "extraction_text": "DashScope 提供 Embedding", "attributes": {"from": "DashScope", "to": "Embedding", "label": "提供"}},
            {"extraction_class": "relation", "extraction_text": "LangExtract 负责实体关系抽取", "attributes": {"from": "LangExtract", "to": "Ke-Hermes", "label": "应用于"}},
        ],
    },
]


def _build_example_data():
    """从字典列表构建 langextract ExampleData 对象。."""
    import langextract as lx

    examples = []
    for ex in _EXTRACTION_EXAMPLES:
        extractions = [
            lx.data.Extraction(
                extraction_class=e["extraction_class"],
                extraction_text=e["extraction_text"],
                attributes=e.get("attributes"),
            )
            for e in ex["extractions"]
        ]
        examples.append(lx.data.ExampleData(text=ex["text"], extractions=extractions))
    return examples


def _convert_extractions(extractions: list) -> tuple[list[dict], list[dict]]:
    """将 langextract 结果转为内部 entity/relation 列表，保留 source grounding 信息。."""
    entities: list[dict] = []
    relations: list[dict] = []

    for e in extractions:
        if e.char_interval is None:
            continue
        if e.extraction_class == "entity":
            entities.append(
                {
                    "name": e.extraction_text,
                    "type": (e.attributes or {}).get("type", "概念"),
                    "source_text": e.extraction_text,
                    "char_start": e.char_interval.start,
                    "char_end": e.char_interval.end,
                }
            )
        elif e.extraction_class == "relation":
            attrs = e.attributes or {}
            from_ent = attrs.get("from", "")
            to_ent = attrs.get("to", "")
            label = attrs.get("label", e.extraction_text)
            if from_ent and to_ent and label:
                relations.append(
                    {
                        "from": from_ent,
                        "to": to_ent,
                        "label": label,
                    }
                )

    return entities, relations


async def get_graph_data(
    db: AsyncSession,
    kb_id: str,
    entity_type: str | None = None,
) -> dict:
    """获取知识图谱数据（实体 + 关系）."""
    entity_stmt = select(KnowledgeBaseEntity).where(KnowledgeBaseEntity.kb_id == kb_id)
    if entity_type:
        entity_stmt = entity_stmt.where(KnowledgeBaseEntity.type == entity_type)
    entity_stmt = entity_stmt.order_by(KnowledgeBaseEntity.mentions.desc())
    entity_rows = (await db.execute(entity_stmt)).scalars().all()

    rel_stmt = select(KnowledgeBaseRelation).where(KnowledgeBaseRelation.kb_id == kb_id)
    rel_stmt = rel_stmt.order_by(KnowledgeBaseRelation.weight.desc())
    relation_rows = (await db.execute(rel_stmt)).scalars().all()

    return {
        "entities": [
            {"id": e.id, "name": e.name, "type": e.type, "mentions": e.mentions}
            for e in entity_rows
        ],
        "relations": [
            {
                "id": r.id,
                "from_entity": r.from_entity,
                "to_entity": r.to_entity,
                "label": r.label,
                "weight": r.weight,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
            }
            for r in relation_rows
        ],
    }


async def get_entity_detail(
    db: AsyncSession, kb_id: str, entity_id: str
) -> dict | None:
    """获取实体详情及关联关系."""
    entity = (
        await db.execute(
            select(KnowledgeBaseEntity).where(
                KnowledgeBaseEntity.id == entity_id,
                KnowledgeBaseEntity.kb_id == kb_id,
            )
        )
    ).scalar_one_or_none()
    if entity is None:
        return None

    relations = (
        (
            await db.execute(
                select(KnowledgeBaseRelation).where(
                    KnowledgeBaseRelation.kb_id == kb_id,
                    (KnowledgeBaseRelation.source_entity_id == entity.id)
                    | (KnowledgeBaseRelation.target_entity_id == entity.id)
                    | (KnowledgeBaseRelation.from_entity == entity.name)
                    | (KnowledgeBaseRelation.to_entity == entity.name),
                )
            )
        )
        .scalars()
        .all()
    )

    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type,
        "mentions": entity.mentions,
        "metadata_": entity.metadata_,
        "source_text": entity.source_text,
        "relations": [
            {
                "id": r.id,
                "from_entity": r.from_entity,
                "to_entity": r.to_entity,
                "label": r.label,
                "weight": r.weight,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
            }
            for r in relations
        ],
    }


class GraphExtractionService:
    """实体/关系抽取服务——使用 LangExtract 框架。."""

    def __init__(self) -> None:
        """初始化抽取服务，构建 few-shot 示例."""
        self._examples = _build_example_data()

    def _build_model_config(self):
        """构建连接 DeepSeek 的 ModelConfig（OpenAI 兼容模式）。.

        DeepSeek 不支持 response_format 参数，通过 format_type=YAML 阻止
        OpenAI Provider 发送该参数。实际输出仍由 lx.extract 的 format_type
        控制为 JSON。
        """
        from langextract.core.data import FormatType
        from langextract.factory import ModelConfig

        return ModelConfig(
            model_id=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro"),
            provider="openai",
            provider_kwargs={
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "format_type": FormatType.YAML,
            },
        )

    async def extract_entities_and_relations(
        self,
        kb_id: str,
        doc_id: str,
        chunks: list,
    ) -> tuple[list[dict], list[dict]]:
        """使用 LangExtract 从文档分片中抽取实体和关系。.

        合并 chunks 文本，通过 lx.extract() 调用 LLM 进行结构化抽取，
        再利用 asyncio.to_thread 避免阻塞事件循环。
        """
        import langextract as lx

        combined = "\n\n".join(
            c.page_content if hasattr(c, "page_content") else str(c) for c in chunks
        )
        if not combined.strip():
            return [], []

        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not set, skipping graph extraction")
            return [], []

        config = self._build_model_config()

        try:
            result = await asyncio.to_thread(
                lx.extract,
                text_or_documents=combined,
                prompt_description=_EXTRACTION_PROMPT,
                examples=self._examples,
                config=config,
                use_schema_constraints=False,
                fence_output=True,
                max_char_buffer=2000,
                max_workers=5,
                extraction_passes=2,
                show_progress=False,
            )
        except Exception:
            logger.exception("LangExtract extraction failed for doc=%s", doc_id)
            return [], []

        if isinstance(result, list):
            result = result[0] if result else None
        if not result or not result.extractions:
            return [], []

        entities, relations = _convert_extractions(result.extractions)

        grounded = sum(1 for e in result.extractions if e.char_interval is not None)
        logger.info(
            "Extracted %d entities, %d relations for doc=%s (%d/%d grounded)",
            len(entities),
            len(relations),
            doc_id,
            grounded,
            len(result.extractions),
        )

        await self._persist(kb_id, entities, relations)
        return entities, relations

    async def _persist(
        self,
        kb_id: str,
        entities: list[dict],
        relations: list[dict],
    ) -> None:
        """将实体和关系写入数据库，关系引用实体 ID 而非仅名称。."""
        from db.engine import async_session

        async with async_session() as db:
            try:
                # Phase 1: Upsert 实体，构建 name -> id 映射
                entity_map: dict[str, str] = {}
                for e in entities:
                    name = e.get("name", "").strip()
                    etype = e.get("type", "概念")
                    if not name:
                        continue
                    if name in entity_map:
                        continue

                    existing = (
                        await db.execute(
                            select(KnowledgeBaseEntity).where(
                                KnowledgeBaseEntity.kb_id == kb_id,
                                KnowledgeBaseEntity.name == name,
                            )
                        )
                    ).scalar_one_or_none()

                    if existing:
                        existing.mentions = (existing.mentions or 0) + 1
                        entity_map[name] = existing.id
                    else:
                        ent_id = str(uuid.uuid4())
                        db.add(
                            KnowledgeBaseEntity(
                                id=ent_id,
                                kb_id=kb_id,
                                name=name,
                                type=etype,
                                mentions=1,
                                source_text=e.get("source_text"),
                                char_start=e.get("char_start"),
                                char_end=e.get("char_end"),
                            )
                        )
                        entity_map[name] = ent_id

                await db.flush()  # 确保实体 ID 已持久化

                # Phase 2: Upsert 关系，使用实体 ID
                for r in relations:
                    from_name = r.get("from", "").strip()
                    to_name = r.get("to", "").strip()
                    label = r.get("label", "").strip()
                    if not from_name or not to_name or not label:
                        continue

                    source_id = entity_map.get(from_name)
                    target_id = entity_map.get(to_name)

                    if not source_id or not target_id:
                        logger.warning(
                            "跳过关系 '%s' -> '%s': 实体端点未找到", from_name, to_name
                        )
                        continue

                    existing_rel = (
                        await db.execute(
                            select(KnowledgeBaseRelation).where(
                                KnowledgeBaseRelation.kb_id == kb_id,
                                KnowledgeBaseRelation.from_entity == from_name,
                                KnowledgeBaseRelation.to_entity == to_name,
                                KnowledgeBaseRelation.label == label,
                            )
                        )
                    ).scalar_one_or_none()

                    if existing_rel:
                        existing_rel.weight = (existing_rel.weight or 1.0) + 1.0
                        if existing_rel.source_entity_id is None:
                            existing_rel.source_entity_id = source_id
                        if existing_rel.target_entity_id is None:
                            existing_rel.target_entity_id = target_id
                    else:
                        db.add(
                            KnowledgeBaseRelation(
                                id=str(uuid.uuid4()),
                                kb_id=kb_id,
                                from_entity=from_name,
                                to_entity=to_name,
                                label=label,
                                weight=1.0,
                                source_entity_id=source_id,
                                target_entity_id=target_id,
                            )
                        )

                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception(
                    "Failed to persist entities/relations for kb=%s", kb_id
                )
