from fastapi import FastAPI
from app.core.config import settings

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": "SaaS backend running",
        "debug": settings.DEBUG,
        "database": settings.DATABASE_URL,
    }