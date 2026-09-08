from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import router
from app.db.base import engine
from app.db.init import init_db
from app.middleware.tenant import TenantContextMiddleware

app = FastAPI(title="Project Aegis", version="1.0.0", description="Secure multi-tenant project management SaaS backend")
app.add_middleware(TenantContextMiddleware)
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "aegis"}


@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"result": result.scalar()}
