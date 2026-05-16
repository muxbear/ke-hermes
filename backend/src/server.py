from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from api import router

app = FastAPI(title="ke-hermes", description="通用智能体服务")
app.include_router(router)