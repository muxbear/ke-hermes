"""技能上传业务逻辑：压缩包解压、校验与安装。"""
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile
import zipfile

import yaml
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from agent.config import settings
from api.skill.schemas import (
    SkillCreateRequest,
    SkillDeleteResponse,
    SkillDeleteResult,
    SkillInfo,
    SkillListResponse,
    SkillResult,
    SkillsUploadResponse,
    SkillUpdateRequest,
    SkillValidationError,
)
from db.models.skill import Skill

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_MB = 100
_SKILL_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

SKILLS_DIR = os.path.join(settings.WORKSPACE, "skills_upload")


def get_skill_upload_path(skill_name: str) -> str:
    """返回技能在上传目录中的文件系统路径。"""
    return os.path.join(SKILLS_DIR, skill_name)


def parse_skill_frontmatter(content: str) -> tuple[dict | None, str | None]:
    """解析 SKILL.md 中的 YAML 前置元数据。

    返回:
        (解析后的字典或 None, 错误信息或 None)。
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None, "SKILL.md 必须以 YAML 前置元数据 (--- ... ---) 开头"

    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return None, f"前置元数据 YAML 格式无效: {e}"

    if not isinstance(parsed, dict):
        return None, "前置元数据必须是 YAML 映射格式"

    return parsed, None


def _read_skill_metadata(skill_path: str) -> tuple[str, str]:
    """从技能的 SKILL.md 前置元数据中读取描述和许可证。

    返回 (description, license)。出错时两者默认为空字符串。
    """
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return "", ""

    try:
        with open(skill_md, encoding="utf-8") as f:
            fm, err = parse_skill_frontmatter(f.read())
        if err or fm is None:
            return "", ""
        desc = fm.get("description", "")
        lic = fm.get("license", "")
        return (
            desc if isinstance(desc, str) else "",
            lic if isinstance(lic, str) else "",
        )
    except OSError:
        return "", ""


def validate_skill_directory(
    skill_path: str, expected_name: str | None = None
) -> SkillResult:
    """按智能体技能规范校验技能目录。

    参数:
        skill_path: 技能目录路径。
        expected_name: 规范技能名称（来自前置元数据）。未提供时回退到目录名。
            当目录为临时解压目录且名称与技能不匹配时使用此参数。
    """
    name = expected_name or os.path.basename(skill_path)
    errors: list[SkillValidationError] = []

    # 1. 校验目录名称格式
    if not _SKILL_NAME_RE.match(name):
        errors.append(
            SkillValidationError(
                field="directory",
                message=f"目录名 '{name}' 无效，必须为 1-64 个字符，"
                "仅允许小写字母、数字和连字符，"
                "不能以连字符开头或结尾。",
            )
        )

    # 2. SKILL.md 必须存在
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        errors.append(
            SkillValidationError(
                field="SKILL.md", message="技能目录中未找到 SKILL.md 文件"
            )
        )
        return SkillResult(name=name, valid=False, errors=errors)

    # 3. 解析前置元数据
    with open(skill_md, encoding="utf-8") as f:
        content = f.read()
    fm, err = parse_skill_frontmatter(content)
    if err:
        errors.append(SkillValidationError(field="SKILL.md", message=err))
        return SkillResult(name=name, valid=False, errors=errors)

    assert fm is not None

    # 4. 必填字段校验
    fm_name = fm.get("name")
    if not fm_name or not isinstance(fm_name, str):
        errors.append(
            SkillValidationError(
                field="name", message="name 为必填字段，且必须为字符串"
            )
        )
    elif not _SKILL_NAME_RE.match(fm_name):
        errors.append(
            SkillValidationError(
                field="name",
                message="name 必须为小写字母、数字和连字符，长度 1-64 个字符",
            )
        )
    elif fm_name != name:
        errors.append(
            SkillValidationError(
                field="name",
                message=f"SKILL.md 中 name '{fm_name}' 与目录名 '{name}' 不一致",
            )
        )

    fm_desc = fm.get("description")
    if not fm_desc or not isinstance(fm_desc, str):
        errors.append(
            SkillValidationError(
                field="description",
                message="description 为必填字段，且必须为字符串",
            )
        )
    elif len(fm_desc) < 1 or len(fm_desc) > 1024:
        errors.append(
            SkillValidationError(
                field="description",
                message=f"description 长度必须为 1-1024 个字符，当前长度为 {len(fm_desc)}",
            )
        )

    # 5. 可选字段类型校验
    if "license" in fm and not isinstance(fm["license"], str):
        errors.append(
            SkillValidationError(field="license", message="license 必须为字符串")
        )
    if "compatibility" in fm and not isinstance(fm["compatibility"], str):
        errors.append(
            SkillValidationError(
                field="compatibility", message="compatibility 必须为字符串"
            )
        )

    # metadata 字段暂不校验，直接跳过
    
    if "allowed-tools" in fm:
        tools = fm["allowed-tools"]
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            errors.append(
                SkillValidationError(
                    field="allowed-tools",
                    message="allowed-tools 必须为字符串列表",
                )
            )

    # 6. 可选子目录校验
    for subdir in ("scripts", "references", "assets"):
        sub_path = os.path.join(skill_path, subdir)
        if os.path.exists(sub_path) and not os.path.isdir(sub_path):
            errors.append(
                SkillValidationError(
                    field=subdir, message=f"{subdir} 必须是目录而非文件"
                )
            )

    return SkillResult(name=name, valid=len(errors) == 0, errors=errors)


def _detect_archive_format(file_path: str) -> str:
    """通过读取文件头魔数检测压缩包格式。

    返回以下格式之一: 'zip'、'tar.gz'、'tar.bz2'、'tar.xz'、'tar'。
    """
    with open(file_path, "rb") as f:
        header = f.read(4)

    if header[:4] == b"PK\x03\x04":
        return "zip"
    if header[:3] == b"\x1f\x8b\x08":
        return "tar.gz"
    if header[:3] == b"BZh":
        return "tar.bz2"
    if header[:4] == b"\xfd7zXZ":
        return "tar.xz"

    with open(file_path, "rb") as f:
        f.seek(257)
        if f.read(5) == b"ustar":
            return "tar"

    raise HTTPException(
        status_code=400,
        detail="不支持的压缩格式，支持: zip, tar.gz, tar.bz2, tar.xz",
    )


def _extract_archive(src_path: str, dest_dir: str, fmt: str) -> None:
    """将压缩包解压到目标目录。"""
    try:
        if fmt == "zip":
            with zipfile.ZipFile(src_path) as zf:
                for member in zf.infolist():
                    # 路径穿越攻击防护
                    member_path = os.path.realpath(
                        os.path.join(dest_dir, member.filename)
                    )
                    if not member_path.startswith(os.path.realpath(dest_dir) + os.sep):
                        raise HTTPException(
                            status_code=400,
                            detail="压缩包包含路径穿越攻击",
                        )
                zf.extractall(dest_dir)
        elif fmt == "tar.gz":
            with tarfile.open(src_path, mode="r:gz") as tf:
                _safe_extract_tar(tf, dest_dir)
        elif fmt == "tar.bz2":
            with tarfile.open(src_path, mode="r:bz2") as tf:
                _safe_extract_tar(tf, dest_dir)
        elif fmt == "tar.xz":
            with tarfile.open(src_path, mode="r:xz") as tf:
                _safe_extract_tar(tf, dest_dir)
        elif fmt == "tar":
            with tarfile.open(src_path, mode="r:") as tf:
                _safe_extract_tar(tf, dest_dir)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"解压失败: {e}"
        ) from e


def _safe_extract_tar(tf: tarfile.TarFile, dest_dir: str) -> None:
    """解压 tar 文件，含路径穿越攻击防护。"""
    for member in tf.getmembers():
        member_path = os.path.realpath(os.path.join(dest_dir, member.name))
        if not member_path.startswith(os.path.realpath(dest_dir) + os.sep):
            raise HTTPException(
                status_code=400, detail="压缩包包含路径穿越攻击"
            )
    tf.extractall(dest_dir)


def _is_skill_dir(path: str) -> bool:
    """检查目录是否包含 SKILL.md（即是否为有效的技能根目录）。"""
    return os.path.isfile(os.path.join(path, "SKILL.md"))


def _get_skill_directories(extract_dir: str) -> list[str]:
    """发现解压目录中的技能目录。

    处理三种结构：
    1. 压缩包本身即为技能 —— extract_dir 自身包含 SKILL.md
    2. 压缩包包含单个技能目录 —— 一个子目录包含 SKILL.md
    3. 压缩包包含多个技能目录 —— 多个子目录包含 SKILL.md
    """
    if not os.path.isdir(extract_dir):
        return []

    # 结构 1：压缩包根目录即为技能
    if _is_skill_dir(extract_dir):
        return [extract_dir]

    # 结构 2 和 3：包含 SKILL.md 的子目录
    entries = sorted(os.listdir(extract_dir))
    skill_dirs = [
        os.path.join(extract_dir, e)
        for e in entries
        if os.path.isdir(os.path.join(extract_dir, e))
        and _is_skill_dir(os.path.join(extract_dir, e))
    ]
    if skill_dirs:
        return skill_dirs

    # 未找到技能目录 —— 回退到原始子目录
    # （某些压缩包的子目录可能没有 SKILL.md，由校验步骤报告）
    return [
        os.path.join(extract_dir, e)
        for e in entries
        if os.path.isdir(os.path.join(extract_dir, e))
    ]


def _get_skill_name(skill_path: str) -> str:
    """获取规范技能名称 —— 优先从 SKILL.md 前置元数据读取，回退到目录名。"""
    skill_md = os.path.join(skill_path, "SKILL.md")
    if os.path.isfile(skill_md):
        try:
            with open(skill_md, encoding="utf-8") as f:
                fm, err = parse_skill_frontmatter(f.read())
            if not err and fm and isinstance(fm.get("name"), str):
                return fm["name"]
        except OSError:
            pass
    return os.path.basename(skill_path)


async def process_skills_upload(
    file: UploadFile, db: AsyncSession
) -> SkillsUploadResponse:
    """上传、解压、校验、安装并持久化压缩包中的技能。"""
    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"文件超过最大限制 {MAX_UPLOAD_SIZE_MB}MB",
        )

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    extract_dir = tempfile.mkdtemp()

    try:
        fmt = _detect_archive_format(tmp_path)
        _extract_archive(tmp_path, extract_dir, fmt)

        skill_dirs = _get_skill_directories(extract_dir)
        if not skill_dirs:
            raise HTTPException(
                status_code=400, detail="压缩包中未找到技能目录"
            )

        os.makedirs(SKILLS_DIR, exist_ok=True)

        results: list[SkillResult] = []
        skipped: list[str] = []

        for skill_path in skill_dirs:
            skill_name = _get_skill_name(skill_path)
            dest_path = os.path.join(SKILLS_DIR, skill_name)

            if os.path.exists(dest_path):
                skipped.append(skill_name)
                continue

            result = validate_skill_directory(skill_path, expected_name=skill_name)
            results.append(result)

            shutil.copytree(skill_path, dest_path)

            description, license_ = _read_skill_metadata(skill_path)
            errors_json = json.dumps([e.model_dump() for e in result.errors]) if not result.valid else ""
            db.add(
                Skill(
                    name=skill_name,
                    valid=result.valid,
                    source="local",
                    description=description,
                    license=license_,
                    validation_errors=errors_json,
                )
            )
            logger.info("已安装技能 '%s' (有效=%s)", skill_name, result.valid)

        valid_count = sum(1 for r in results if r.valid)
        invalid_count = len(results) - valid_count

        return SkillsUploadResponse(
            skills_dir=SKILLS_DIR,
            total=len(skill_dirs),
            valid_count=valid_count,
            invalid_count=invalid_count,
            skipped_count=len(skipped),
            results=results,
            skipped=skipped,
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)


async def list_skills(
    db: AsyncSession, page: int = 1, page_size: int = 20, category: str | None = None, enabled: bool | None = None
) -> SkillListResponse:
    """分页列出技能，支持按分类和启用状态筛选。"""
    from sqlalchemy import func, select

    offset = max(0, (page - 1) * page_size)
    page_size = max(1, min(page_size, 100))

    conditions = []
    if category:
        conditions.append(Skill.category == category)
    if enabled is not None:
        conditions.append(Skill.enabled == enabled)

    total_stmt = select(func.count()).select_from(Skill)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = select(Skill).order_by(Skill.created_at.desc()).offset(offset).limit(page_size)
    if conditions:
        stmt = stmt.where(*conditions)
    rows = (await db.execute(stmt)).scalars().all()

    return SkillListResponse(
        items=[SkillInfo.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def search_skills(
    db: AsyncSession,
    name: str,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    enabled: bool | None = None,
) -> SkillListResponse:
    """按名称模糊搜索技能，支持分页和可选筛选。"""
    from sqlalchemy import func, select

    offset = max(0, (page - 1) * page_size)
    page_size = max(1, min(page_size, 100))
    pattern = f"%{name}%"

    conditions: list = [Skill.name.like(pattern)]
    if category:
        conditions.append(Skill.category == category)
    if enabled is not None:
        conditions.append(Skill.enabled == enabled)

    total_stmt = select(func.count()).select_from(Skill).where(*conditions)
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = (
        select(Skill)
        .where(*conditions)
        .order_by(Skill.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return SkillListResponse(
        items=[SkillInfo.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


async def _delete_one_skill(db: AsyncSession, skill_id: str) -> SkillDeleteResult:
    """按 ID 删除单个技能 —— 同时删除数据库记录和文件系统目录。"""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()

    if row is None:
        return SkillDeleteResult(id=skill_id, name="", deleted=False, reason="未找到")

    name = row.name
    await db.delete(row)

    skill_dir = os.path.join(SKILLS_DIR, name)
    if os.path.isdir(skill_dir):
        shutil.rmtree(skill_dir, ignore_errors=True)
        logger.info("已删除技能 '%s' (id=%s)", name, skill_id)

    # 清理所有智能体技能目录中的副本
    agent_skills_root = os.path.join(settings.WORKSPACE, "skills")
    if os.path.isdir(agent_skills_root):
        for agent_dir in os.listdir(agent_skills_root):
            agent_skill_path = os.path.join(agent_skills_root, agent_dir, name)
            if os.path.isdir(agent_skill_path):
                shutil.rmtree(agent_skill_path, ignore_errors=True)
                logger.info(
                    "已清理智能体技能 '%s/%s'", agent_dir, name
                )

    return SkillDeleteResult(id=skill_id, name=name, deleted=True)


async def delete_skill(db: AsyncSession, skill_id: str) -> SkillDeleteResponse:
    """按 ID 删除单个技能。"""
    result = await _delete_one_skill(db, skill_id)
    return SkillDeleteResponse(
        deleted_count=1 if result.deleted else 0,
        failed_count=0 if result.deleted else 1,
        results=[result],
    )


async def delete_skills_batch(
    db: AsyncSession, ids: list[str]
) -> SkillDeleteResponse:
    """按 ID 列表批量删除技能。"""
    results: list[SkillDeleteResult] = []
    for skill_id in ids:
        result = await _delete_one_skill(db, skill_id)
        results.append(result)

    deleted_count = sum(1 for r in results if r.deleted)
    failed_count = len(results) - deleted_count
    return SkillDeleteResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        results=results,
    )


async def get_skill(db: AsyncSession, skill_id: str) -> SkillInfo:
    """按 ID 获取单个技能。"""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="技能未找到")
    return SkillInfo.model_validate(row)


async def update_skill(
    db: AsyncSession, skill_id: str, req: SkillUpdateRequest
) -> SkillInfo:
    """更新技能元数据，仅更新非 None 字段。"""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="技能未找到")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(row, key, value)

    return SkillInfo.model_validate(row)


async def toggle_skill_enabled(
    db: AsyncSession, skill_id: str, enabled: bool
) -> SkillInfo:
    """切换技能的启用/禁用状态。"""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="技能未找到")

    row.enabled = enabled
    return SkillInfo.model_validate(row)


async def create_skill(
    db: AsyncSession, req: SkillCreateRequest
) -> SkillInfo:
    """手动创建单个技能 —— 写入 SKILL.md 并在数据库中插入记录。"""
    from sqlalchemy import select

    # 检查名称是否重复
    existing = (await db.execute(select(Skill).where(Skill.name == req.name))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"技能 '{req.name}' 已存在")

    # 创建工作区目录和 SKILL.md
    skill_dir = os.path.join(SKILLS_DIR, req.name)
    os.makedirs(skill_dir, exist_ok=True)

    frontmatter = f"---\nname: {req.name}\ndescription: {req.description or ''}\n---\n"
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    skill = Skill(
        name=req.name,
        valid=True,
        source="local",
        description=req.description or "",
        icon=req.icon or "Zap",
        category=req.category or "custom",
        prompt=req.prompt or "",
        enabled=True,
        is_builtin=False,
    )
    db.add(skill)
    logger.info("已创建技能 '%s' (手动)", req.name)

    return SkillInfo.model_validate(skill)


BUILTIN_SKILLS = [
    {
        "name": "网络搜索",
        "description": "实时搜索互联网信息，获取最新数据",
        "icon": "Globe",
        "category": "search",
        "prompt": "你是一个网络搜索专家，能够实时搜索互联网获取最新数据和信息。",
    },
    {
        "name": "代码解释器",
        "description": "在安全沙箱中执行代码，支持数据分析",
        "icon": "Code2",
        "category": "code",
        "prompt": "你是一个代码执行专家，能够在安全沙箱环境中执行代码并返回结果。",
    },
    {
        "name": "图像生成",
        "description": "根据文本描述生成高质量图像",
        "icon": "Image",
        "category": "creative",
        "prompt": "你是一个图像生成专家，能够根据文本描述创作高质量的图像作品。",
    },
    {
        "name": "数据分析",
        "description": "处理结构化数据，生成统计报告和图表",
        "icon": "BarChart3",
        "category": "analysis",
        "prompt": "你是一个数据分析专家，能够处理结构化数据并生成统计报告和可视化图表。",
    },
    {
        "name": "文件管理",
        "description": "读写多种格式文件，支持批量处理",
        "icon": "FolderOpen",
        "category": "tools",
        "prompt": "你是一个文件管理专家，能够读写多种格式的文件并支持批量处理操作。",
    },
    {
        "name": "kb-search",
        "description": "知识库知识检索 —— 支持 RRF 混合检索、向量检索和 BM25 关键词检索",
        "icon": "Search",
        "category": "search",
        "prompt": (
            "你是一个知识库检索专家。当用户的问题需要从已索引的知识库中查找信息时，"
            "使用 kb_search 工具进行搜索。支持的检索模式：hybrid（RRF混合，默认）、"
            "vector（语义）、bm25（关键词）。空结果时尝试更换模式或关键词后重试。"
        ),
    },
]


async def seed_builtin_skills(db: AsyncSession) -> None:
    """填充内置技能，仅当技能表为空时执行，可重复调用。"""
    from sqlalchemy import func, select

    count = (await db.execute(select(func.count()).select_from(Skill))).scalar() or 0
    if count > 0:
        logger.info("技能表已有 %d 条记录，跳过种子数据", count)
        return

    for s in BUILTIN_SKILLS:
        skill = Skill(
            name=s["name"],
            description=s["description"],
            icon=s["icon"],
            category=s["category"],
            prompt=s["prompt"],
            enabled=True,
            is_builtin=True,
            valid=True,
            source="builtin",
        )
        db.add(skill)

    logger.info("已填充 %d 个内置技能", len(BUILTIN_SKILLS))
