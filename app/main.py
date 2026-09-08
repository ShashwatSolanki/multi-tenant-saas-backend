from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.access_control import router as access_control_router
from app.api.routes import router
from app.api.user_admin import router as user_admin_router
from app.db.base import engine
from app.db.init import init_db
from app.middleware.tenant import TenantContextMiddleware

app = FastAPI(title="Project Aegis", version="1.0.0", description="Secure multi-tenant project management SaaS backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantContextMiddleware)

# Register scoped GET/PATCH routes before the legacy/general routes so the
# same public API paths apply the stricter Member visibility policy.
app.include_router(access_control_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")
app.include_router(user_admin_router, prefix="/api/v1")


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
