"""知识图谱服务——LLM Prompt-based 实体/关系抽取 & 查询。"""

import json
import logging
import os
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.knowledge_base_entity import KnowledgeBaseEntity
from db.models.knowledge_base_relation import KnowledgeBaseRelation

logger = logging.getLogger(__name__)

ENTITY_RELATION_PROMPT = """你是一个知识图谱抽取助手。请从以下文本中提取实体和实体之间的关系。

输出 JSON 格式:
{{
  "entities": [{{"name": "实体名", "type": "类型"}}],
  "relations": [{{"from": "实体A", "to": "实体B", "label": "关系"}}]
}}

实体类型必须是: 人物, 组织, 产品, 概念, 算法, 地点, 时间, 事件
只提取有明确关系的实体，不要虚构关系。每个关系中的 from/to 必须出现在 entities 列表中。
文本:
{text}"""


async def get_graph_data(
    db: AsyncSession, kb_id: str, entity_type: str | None = None,
) -> dict:
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
            {"id": r.id, "from": r.from_entity, "to": r.to_entity,
             "label": r.label, "weight": r.weight}
            for r in relation_rows
        ],
    }


async def get_entity_detail(db: AsyncSession, kb_id: str, entity_id: str) -> dict | None:
    entity = (await db.execute(
        select(KnowledgeBaseEntity).where(
            KnowledgeBaseEntity.id == entity_id, KnowledgeBaseEntity.kb_id == kb_id,
        )
    )).scalar_one_or_none()
    if entity is None:
        return None

    relations = (await db.execute(
        select(KnowledgeBaseRelation).where(
            KnowledgeBaseRelation.kb_id == kb_id,
            (KnowledgeBaseRelation.from_entity == entity.name)
            | (KnowledgeBaseRelation.to_entity == entity.name),
        )
    )).scalars().all()

    return {
        "id": entity.id, "name": entity.name, "type": entity.type,
        "mentions": entity.mentions, "metadata_": entity.metadata_,
        "relations": [
            {"id": r.id, "from": r.from_entity, "to": r.to_entity,
             "label": r.label, "weight": r.weight}
            for r in relations
        ],
    }


class GraphExtractionService:
    """实体/关系抽取服务——使用 LLM Prompt-based 抽取。"""

    def __init__(self, backend: str = "langextract"):
        self._backend = backend

    async def extract_entities_and_relations(
        self, kb_id: str, doc_id: str, chunks: list,
    ) -> tuple[list[dict], list[dict]]:
        """从文档分片中抽取实体和关系。

        使用 LLM prompt-based 抽取。合并所有 chunks 做一次全量抽取，
        避免多次 LLM 调用产生的碎片化和高成本。
        """
        # 合并前 8 个 chunk 用于抽取（限制 token 用量）
        max_chunks = min(len(chunks), 8)
        combined = "\n\n".join(
            c.page_content if hasattr(c, "page_content") else str(c)
            for c in chunks[:max_chunks]
        )
        if not combined.strip():
            return [], []

        llm = await self._get_llm()
        if llm is None:
            logger.warning("No LLM available for graph extraction")
            return [], []

        try:
            from langchain_core.messages import HumanMessage
            prompt = ENTITY_RELATION_PROMPT.format(text=combined)
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            text = response.content if hasattr(response, "content") else str(response)
            parsed = self._parse_json(text)
        except Exception as e:
            logger.exception("LLM extraction failed for doc=%s", doc_id)
            return [], []

        if not parsed:
            return [], []

        entities = parsed.get("entities", [])
        relations = parsed.get("relations", [])

        # Persist to DB
        await self._persist(kb_id, entities, relations)

        logger.info("Extracted %d entities, %d relations for doc=%s",
                     len(entities), len(relations), doc_id)
        return entities, relations

    async def _get_llm(self):
        """获取 LLM 实例（优先用默认 DeepSeek）。"""
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro"),
                openai_api_base=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                openai_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                temperature=0.1,
            )
        except Exception as e:
            logger.error("Failed to create LLM: %s", e)
            return None

    def _parse_json(self, text: str) -> dict | None:
        """从 LLM 响应中解析 JSON。支持 ```json 代码块包裹。"""
        # 提取 ```json ... ``` 中的内容
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试匹配裸 JSON 对象
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse LLM JSON response: %s", text[:200])
            return None

    async def _persist(
        self, kb_id: str, entities: list[dict], relations: list[dict],
    ) -> None:
        """将实体和关系写入数据库。"""
        from db.engine import async_session

        async with async_session() as db:
            try:
                # Upsert entities
                entity_map: dict[str, str] = {}  # name → entity_id
                for e in entities:
                    name = e.get("name", "").strip()
                    etype = e.get("type", "概念")
                    if not name:
                        continue
                    if name in entity_map:
                        continue

                    existing = (await db.execute(
                        select(KnowledgeBaseEntity).where(
                            KnowledgeBaseEntity.kb_id == kb_id,
                            KnowledgeBaseEntity.name == name,
                        )
                    )).scalar_one_or_none()

                    if existing:
                        existing.mentions = (existing.mentions or 0) + 1
                        entity_map[name] = existing.id
                    else:
                        ent_id = str(uuid.uuid4())
                        db.add(KnowledgeBaseEntity(
                            id=ent_id, kb_id=kb_id, name=name, type=etype, mentions=1,
                        ))
                        entity_map[name] = ent_id

                # Insert relations
                for r in relations:
                    from_name = r.get("from", "").strip()
                    to_name = r.get("to", "").strip()
                    label = r.get("label", "").strip()
                    if not from_name or not to_name or not label:
                        continue

                    existing_rel = (await db.execute(
                        select(KnowledgeBaseRelation).where(
                            KnowledgeBaseRelation.kb_id == kb_id,
                            KnowledgeBaseRelation.from_entity == from_name,
                            KnowledgeBaseRelation.to_entity == to_name,
                            KnowledgeBaseRelation.label == label,
                        )
                    )).scalar_one_or_none()

                    if not existing_rel:
                        db.add(KnowledgeBaseRelation(
                            id=str(uuid.uuid4()), kb_id=kb_id,
                            from_entity=from_name, to_entity=to_name,
                            label=label, weight=1.0,
                        ))

                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.exception("Failed to persist entities/relations for kb=%s", kb_id)
