import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

load_dotenv()

from api import router
from api.deps import set_store
from core.store import create_store
from db.engine import init_db
from agent.graph import init_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_graph()
    store = await create_store()
    set_store(store)
    from core.security import _get_jwt_secret as init_jwt
    init_jwt()  # 预初始化 JWT secret，确保重启后不变
    yield


app = FastAPI(
    title="ke-hermes",
    description="通用智能体服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
