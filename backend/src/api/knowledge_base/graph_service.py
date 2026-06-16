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
    实体类型必须是: 人物、组织、产品、概念、算法、地点、时间、事件。
    每个 entity 的 extraction_text 必须是原文中的精确文本片段。
    每个 relation 的 extraction_text 描述两个实体的关系，attributes 中写明 from/to/label.""")

_EXTRACTION_EXAMPLES = [
    {
        "text": (
            "2024年3月，张明加入阿里巴巴达摩院，担任NLP研究科学家。"
            "他主导开发了大规模语言模型「通义千问」，该模型在多项基准测试中表现优异。"
            "阿里巴巴总部位于杭州，由马云于1999年创立。"
        ),
        "extractions": [
            {
                "extraction_class": "entity",
                "extraction_text": "张明",
                "attributes": {"type": "人物"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "阿里巴巴达摩院",
                "attributes": {"type": "组织"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "NLP研究科学家",
                "attributes": {"type": "概念"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "通义千问",
                "attributes": {"type": "产品"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "大规模语言模型",
                "attributes": {"type": "概念"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "杭州",
                "attributes": {"type": "地点"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "马云",
                "attributes": {"type": "人物"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "1999年",
                "attributes": {"type": "时间"},
            },
            {
                "extraction_class": "entity",
                "extraction_text": "2024年3月",
                "attributes": {"type": "时间"},
            },
            {
                "extraction_class": "relation",
                "extraction_text": "张明加入阿里巴巴达摩院",
                "attributes": {
                    "from": "张明",
                    "to": "阿里巴巴达摩院",
                    "label": "任职于",
                },
            },
            {
                "extraction_class": "relation",
                "extraction_text": "张明主导开发通义千问",
                "attributes": {"from": "张明", "to": "通义千问", "label": "开发"},
            },
            {
                "extraction_class": "relation",
                "extraction_text": "阿里巴巴总部位于杭州",
                "attributes": {"from": "阿里巴巴达摩院", "to": "杭州", "label": "位于"},
            },
            {
                "extraction_class": "relation",
                "extraction_text": "马云创立阿里巴巴",
                "attributes": {"from": "马云", "to": "阿里巴巴达摩院", "label": "创立"},
            },
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
    """将 langextract 结果转为内部 entity/relation 列表。."""
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
                "from": r.from_entity,
                "to": r.to_entity,
                "label": r.label,
                "weight": r.weight,
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
                    (KnowledgeBaseRelation.from_entity == entity.name)
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
        "relations": [
            {
                "id": r.id,
                "from": r.from_entity,
                "to": r.to_entity,
                "label": r.label,
                "weight": r.weight,
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
                extraction_passes=1,
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
        """将实体和关系写入数据库。."""
        from db.engine import async_session

        async with async_session() as db:
            try:
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
                            )
                        )
                        entity_map[name] = ent_id

                for r in relations:
                    from_name = r.get("from", "").strip()
                    to_name = r.get("to", "").strip()
                    label = r.get("label", "").strip()
                    if not from_name or not to_name or not label:
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

                    if not existing_rel:
                        db.add(
                            KnowledgeBaseRelation(
                                id=str(uuid.uuid4()),
                                kb_id=kb_id,
                                from_entity=from_name,
                                to_entity=to_name,
                                label=label,
                                weight=1.0,
                            )
                        )

                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.exception(
                    "Failed to persist entities/relations for kb=%s", kb_id
                )
