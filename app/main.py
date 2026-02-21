from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.api.routes import auth

app = FastAPI()
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}