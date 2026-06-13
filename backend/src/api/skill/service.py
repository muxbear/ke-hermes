"""Skill upload business logic: archive extraction, validation, and installation."""
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
    """Return the filesystem path for a skill in the upload catalog."""
    return os.path.join(SKILLS_DIR, skill_name)


def parse_skill_frontmatter(content: str) -> tuple[dict | None, str | None]:
    """Parse YAML frontmatter from SKILL.md content.

    Returns:
        Tuple of (parsed_dict_or_None, error_message_or_None).
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
    """Read description and license from a skill's SKILL.md frontmatter.

    Returns (description, license). Both default to empty strings on any error.
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
    """Validate a skill directory against the Agent Skills specification.

    Args:
        skill_path: Path to the skill directory.
        expected_name: Canonical skill name (from frontmatter). When not provided,
            falls back to the directory name. Use this when the directory is a
            temp extraction directory whose name doesn't match the skill.
    """
    name = expected_name or os.path.basename(skill_path)
    errors: list[SkillValidationError] = []

    # 1. Validate directory name format
    if not _SKILL_NAME_RE.match(name):
        errors.append(
            SkillValidationError(
                field="directory",
                message=f"目录名 '{name}' 无效，必须为 1-64 个字符，"
                "仅允许小写字母、数字和连字符，"
                "不能以连字符开头或结尾。",
            )
        )

    # 2. SKILL.md must exist
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        errors.append(
            SkillValidationError(
                field="SKILL.md", message="技能目录中未找到 SKILL.md 文件"
            )
        )
        return SkillResult(name=name, valid=False, errors=errors)

    # 3. Parse frontmatter
    with open(skill_md, encoding="utf-8") as f:
        content = f.read()
    fm, err = parse_skill_frontmatter(content)
    if err:
        errors.append(SkillValidationError(field="SKILL.md", message=err))
        return SkillResult(name=name, valid=False, errors=errors)

    assert fm is not None

    # 4. Required fields
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

    # 5. Optional fields type validation
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

    # 6. Optional subdirectories
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
    """Detect archive format by reading magic bytes.

    Returns one of: 'zip', 'tar.gz', 'tar.bz2', 'tar.xz', 'tar'.
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
        detail="Unsupported archive format. Supported: zip, tar.gz, tar.bz2, tar.xz",
    )


def _extract_archive(src_path: str, dest_dir: str, fmt: str) -> None:
    """Extract an archive into dest_dir."""
    try:
        if fmt == "zip":
            with zipfile.ZipFile(src_path) as zf:
                for member in zf.infolist():
                    # Path traversal protection
                    member_path = os.path.realpath(
                        os.path.join(dest_dir, member.filename)
                    )
                    if not member_path.startswith(os.path.realpath(dest_dir) + os.sep):
                        raise HTTPException(
                            status_code=400,
                            detail="Archive contains path traversal attack",
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
            status_code=400, detail=f"Failed to extract archive: {e}"
        ) from e


def _safe_extract_tar(tf: tarfile.TarFile, dest_dir: str) -> None:
    """Extract tar with path traversal protection."""
    for member in tf.getmembers():
        member_path = os.path.realpath(os.path.join(dest_dir, member.name))
        if not member_path.startswith(os.path.realpath(dest_dir) + os.sep):
            raise HTTPException(
                status_code=400, detail="Archive contains path traversal attack"
            )
    tf.extractall(dest_dir)


def _is_skill_dir(path: str) -> bool:
    """Check whether a directory contains a SKILL.md (i.e. is a valid skill root)."""
    return os.path.isfile(os.path.join(path, "SKILL.md"))


def _get_skill_directories(extract_dir: str) -> list[str]:
    """Discover skill directories inside an extracted archive.

    Handles three layouts:
    1. Archive IS a skill — extract_dir itself contains SKILL.md
    2. Archive contains a single skill dir — one subdir with SKILL.md
    3. Archive contains multiple skill dirs — several subdirs with SKILL.md
    """
    if not os.path.isdir(extract_dir):
        return []

    # Layout 1: archive root is a skill
    if _is_skill_dir(extract_dir):
        return [extract_dir]

    # Layout 2 & 3: subdirectories that contain SKILL.md
    entries = sorted(os.listdir(extract_dir))
    skill_dirs = [
        os.path.join(extract_dir, e)
        for e in entries
        if os.path.isdir(os.path.join(extract_dir, e))
        and _is_skill_dir(os.path.join(extract_dir, e))
    ]
    if skill_dirs:
        return skill_dirs

    # No skill directories found — fall back to raw subdirectories
    # (some archives may have subdirs without SKILL.md, let validation report that)
    return [
        os.path.join(extract_dir, e)
        for e in entries
        if os.path.isdir(os.path.join(extract_dir, e))
    ]


def _get_skill_name(skill_path: str) -> str:
    """Get the canonical skill name — from SKILL.md frontmatter, or fallback to dirname."""
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
    """Upload, extract, validate, install, and persist skills from a compressed archive."""
    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_SIZE_MB}MB",
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
                status_code=400, detail="Archive contains no skill directories"
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
            logger.info("Installed skill '%s' (valid=%s)", skill_name, result.valid)

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
    """List skills with pagination and optional category/enabled filters."""
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
    """Fuzzy-search skills by name, with pagination and optional filters."""
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
    """Delete a single skill by ID — removes DB record and filesystem directory."""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()

    if row is None:
        return SkillDeleteResult(id=skill_id, name="", deleted=False, reason="not found")

    name = row.name
    await db.delete(row)

    skill_dir = os.path.join(SKILLS_DIR, name)
    if os.path.isdir(skill_dir):
        shutil.rmtree(skill_dir, ignore_errors=True)
        logger.info("Deleted skill '%s' (id=%s)", name, skill_id)

    # Clean up copies from all agents' skills directories
    agent_skills_root = os.path.join(settings.WORKSPACE, "skills")
    if os.path.isdir(agent_skills_root):
        for agent_dir in os.listdir(agent_skills_root):
            agent_skill_path = os.path.join(agent_skills_root, agent_dir, name)
            if os.path.isdir(agent_skill_path):
                shutil.rmtree(agent_skill_path, ignore_errors=True)
                logger.info(
                    "Cleaned up agent skill '%s/%s'", agent_dir, name
                )

    return SkillDeleteResult(id=skill_id, name=name, deleted=True)


async def delete_skill(db: AsyncSession, skill_id: str) -> SkillDeleteResponse:
    """Delete a single skill by ID."""
    result = await _delete_one_skill(db, skill_id)
    return SkillDeleteResponse(
        deleted_count=1 if result.deleted else 0,
        failed_count=0 if result.deleted else 1,
        results=[result],
    )


async def delete_skills_batch(
    db: AsyncSession, ids: list[str]
) -> SkillDeleteResponse:
    """Batch-delete skills by ID list."""
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
    """Get a single skill by ID."""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillInfo.model_validate(row)


async def update_skill(
    db: AsyncSession, skill_id: str, req: SkillUpdateRequest
) -> SkillInfo:
    """Update skill metadata. Only non-None fields are updated."""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(row, key, value)

    return SkillInfo.model_validate(row)


async def toggle_skill_enabled(
    db: AsyncSession, skill_id: str, enabled: bool
) -> SkillInfo:
    """Toggle a skill's enabled state."""
    from sqlalchemy import select

    stmt = select(Skill).where(Skill.id == skill_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    row.enabled = enabled
    return SkillInfo.model_validate(row)


async def create_skill(
    db: AsyncSession, req: SkillCreateRequest
) -> SkillInfo:
    """Create a single skill manually — writes SKILL.md and inserts DB record."""
    from sqlalchemy import select

    # Check for duplicate name
    existing = (await db.execute(select(Skill).where(Skill.name == req.name))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Skill '{req.name}' already exists")

    # Create workspace directory and SKILL.md
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
    logger.info("Created skill '%s' (manual)", req.name)

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
]


async def seed_builtin_skills(db: AsyncSession) -> None:
    """Seed builtin skills if the skills table is empty. Idempotent."""
    from sqlalchemy import func, select

    count = (await db.execute(select(func.count()).select_from(Skill))).scalar() or 0
    if count > 0:
        logger.info("Skills table has %d rows, skipping seed", count)
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

    logger.info("Seeded %d builtin skills", len(BUILTIN_SKILLS))
