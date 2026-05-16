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
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c