from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine

from app.api.routes import auth
from app.middleware.auth import AuthMiddleware
from app.middleware.tenant import TenantMiddleware
from app.middleware.rbac import RBACMiddleware

app = FastAPI()

# Middleware Order Matters
app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(RBACMiddleware)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok"}