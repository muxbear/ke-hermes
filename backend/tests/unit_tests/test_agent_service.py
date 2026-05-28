"""Unit tests for agent service layer."""
import pytest
from sqlalchemy import func, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.agents.schemas import AgentConfigRequest, AgentCreateRequest
from api.agents.service import (
    add_agent_config,
    clone_agent,
    create_agent,
    delete_agent,
    get_agent,
    list_agents,
    remove_agent_config,
    toggle_agent_status,
)
from db.base import Base
from db.models.agent import Agent

pytestmark = pytest.mark.anyio

USER_ID = "test-user-1"


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite session with tables created."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _create_main_agent(db: AsyncSession) -> str:
    """Helper: create a default main agent and return its ID."""
    info = await create_agent(
        db, AgentCreateRequest(name="主智能体", description="主代理"), USER_ID
    )
    return info.id


# ---- create_agent ----


async def test_create_main_agent(db_session: AsyncSession):
    info = await create_agent(
        db_session, AgentCreateRequest(name="主智能体", description="测试"), USER_ID
    )
    assert info.name == "主智能体"
    assert info.type == "main"
    assert info.status == "inactive"


async def test_create_main_agent_duplicate_name(db_session: AsyncSession):
    await create_agent(db_session, AgentCreateRequest(name="主智能体"), USER_ID)
    with pytest.raises(Exception) as exc:
        await create_agent(db_session, AgentCreateRequest(name="主智能体"), USER_ID)
    assert exc.value.status_code == 409


async def test_create_second_main_agent_fails(db_session: AsyncSession):
    await create_agent(db_session, AgentCreateRequest(name="主1"), USER_ID)
    with pytest.raises(Exception) as exc:
        await create_agent(db_session, AgentCreateRequest(name="主2"), USER_ID)
    assert exc.value.status_code == 409


async def test_create_sub_agent(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    info = await create_agent(
        db_session,
        AgentCreateRequest(name="子代理", parent_id=main_id),
        USER_ID,
    )
    assert info.type == "sub"
    assert info.parent_id == main_id


async def test_create_sub_agent_nonexistent_parent(db_session: AsyncSession):
    with pytest.raises(Exception) as exc:
        await create_agent(
            db_session,
            AgentCreateRequest(name="子代理", parent_id="nonexistent"),
            USER_ID,
        )
    assert exc.value.status_code == 404


# ---- list_agents ----


async def test_list_agents_auto_seeds(db_session: AsyncSession):
    """First call to list_agents auto-creates a default main agent."""
    result = await list_agents(db_session, USER_ID)
    assert len(result.agents) == 1
    assert result.agents[0].name == "主智能体"
    assert result.agents[0].type == "main"
    assert result.agents[0].undeletable is True
    assert result.agents[0].status == "active"


async def test_list_agents_with_sub(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    await create_agent(
        db_session,
        AgentCreateRequest(name="子1", parent_id=main_id),
        USER_ID,
    )
    await create_agent(
        db_session,
        AgentCreateRequest(name="子2", parent_id=main_id),
        USER_ID,
    )
    result = await list_agents(db_session, USER_ID)
    main = next(a for a in result.agents if a.type == "main")
    assert len(main.sub_agents) == 2


# ---- get_agent ----


async def test_get_agent(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    info = await get_agent(db_session, main_id, USER_ID)
    assert info.id == main_id


async def test_get_agent_not_found(db_session: AsyncSession):
    with pytest.raises(Exception) as exc:
        await get_agent(db_session, "nonexistent", USER_ID)
    assert exc.value.status_code == 404


# ---- delete_agent ----


async def test_delete_agent(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    sub = await create_agent(
        db_session,
        AgentCreateRequest(name="子代理", parent_id=main_id),
        USER_ID,
    )
    await delete_agent(db_session, sub.id, USER_ID)
    result = await list_agents(db_session, USER_ID)
    assert len(result.agents) == 1


async def test_delete_undeletable_agent(db_session: AsyncSession):
    # list_agents auto-seeds an undeletable agent
    result = await list_agents(db_session, USER_ID)
    main_id = result.agents[0].id
    with pytest.raises(Exception) as exc:
        await delete_agent(db_session, main_id, USER_ID)
    assert exc.value.status_code == 403


async def test_delete_main_agent_cascades(db_session: AsyncSession):
    """Delete main agent cascades to subs. Use unique user to avoid auto-seed."""
    cascade_user = "cascade-test-user"
    main_id = (await create_agent(
        db_session, AgentCreateRequest(name="主"), cascade_user
    )).id
    await create_agent(
        db_session,
        AgentCreateRequest(name="子1", parent_id=main_id),
        cascade_user,
    )
    await create_agent(
        db_session,
        AgentCreateRequest(name="子2", parent_id=main_id),
        cascade_user,
    )
    # Make main deletable via ORM
    from sqlalchemy import select as sa_select

    stmt = sa_select(Agent).where(Agent.id == main_id)
    agent = (await db_session.execute(stmt)).scalar_one()
    agent.undeletable = False

    await delete_agent(db_session, main_id, cascade_user)
    # Query directly — no auto-seed since we check count == 0
    count_stmt = sa_select(func.count()).select_from(Agent).where(Agent.user_id == cascade_user)
    remaining = (await db_session.execute(count_stmt)).scalar()
    assert remaining == 0


# ---- toggle_agent_status ----


async def test_toggle_status_active_inactive(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    # inactivate -> active
    active = await toggle_agent_status(db_session, main_id, USER_ID)
    assert active.status == "active"
    # active -> inactive
    inactive = await toggle_agent_status(db_session, main_id, USER_ID)
    assert inactive.status == "inactive"


async def test_toggle_status_error_to_inactive(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    # Set status to error via ORM
    stmt = sa_select(Agent).where(Agent.id == main_id)
    agent = (await db_session.execute(stmt)).scalar_one()
    agent.status = "error"
    await db_session.flush()

    info = await toggle_agent_status(db_session, main_id, USER_ID)
    assert info.status == "inactive"


# ---- clone_agent ----


async def test_clone_agent(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    # Add some configs to the main agent
    await add_agent_config(
        db_session, main_id, AgentConfigRequest(type="tool", value="test_tool"), USER_ID
    )
    cloned = await clone_agent(db_session, main_id, USER_ID)
    assert "test_tool" in cloned.tools
    assert cloned.status == "inactive"
    assert cloned.name != "主智能体"


async def test_clone_deduplicates_name(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    c1 = await clone_agent(db_session, main_id, USER_ID)
    c2 = await clone_agent(db_session, main_id, USER_ID)
    assert c1.name != c2.name


# ---- config management ----


async def test_add_config_tool(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    info = await add_agent_config(
        db_session, main_id, AgentConfigRequest(type="tool", value="web_search"), USER_ID
    )
    assert "web_search" in info.tools


async def test_add_config_duplicate(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    await add_agent_config(
        db_session, main_id, AgentConfigRequest(type="tool", value="web_search"), USER_ID
    )
    info = await add_agent_config(
        db_session, main_id, AgentConfigRequest(type="tool", value="web_search"), USER_ID
    )
    assert info.tools.count("web_search") == 1


async def test_remove_config(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    await add_agent_config(
        db_session, main_id, AgentConfigRequest(type="skill", value="debugging"), USER_ID
    )
    info = await remove_agent_config(
        db_session, main_id, AgentConfigRequest(type="skill", value="debugging"), USER_ID
    )
    assert "debugging" not in info.skills


async def test_add_subagent_via_config(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    info = await add_agent_config(
        db_session,
        main_id,
        AgentConfigRequest(type="subagent", value="新子代理"),
        USER_ID,
    )
    assert len(info.sub_agents) == 1


async def test_add_subagent_via_config_on_sub_fails(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    sub = await create_agent(
        db_session,
        AgentCreateRequest(name="子", parent_id=main_id),
        USER_ID,
    )
    with pytest.raises(Exception) as exc:
        await add_agent_config(
            db_session,
            sub.id,
            AgentConfigRequest(type="subagent", value="孙代理"),
            USER_ID,
        )
    assert exc.value.status_code == 400


async def test_remove_subagent_via_config(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    sub = await create_agent(
        db_session,
        AgentCreateRequest(name="子代理", parent_id=main_id),
        USER_ID,
    )
    info = await remove_agent_config(
        db_session,
        main_id,
        AgentConfigRequest(type="subagent", value=sub.id),
        USER_ID,
    )
    assert sub.id not in info.sub_agents


async def test_invalid_config_type(db_session: AsyncSession):
    main_id = await _create_main_agent(db_session)
    with pytest.raises(Exception) as exc:
        await add_agent_config(
            db_session,
            main_id,
            AgentConfigRequest(type="invalid", value="x"),
            USER_ID,
        )
    assert exc.value.status_code == 400
