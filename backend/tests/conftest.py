import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv

load_dotenv()

import pytest
from httpx import ASGITransport, AsyncClient

from server import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):  # triggers init_db + init_graph
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c