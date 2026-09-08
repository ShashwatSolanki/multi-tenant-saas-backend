from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Resolve tenant context early without replacing database-side authorization."""

    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = None
        request.state.user_id = None
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            try:
                payload = decode_access_token(auth.split(" ", 1)[1])
                request.state.tenant_id = payload.get("tenant_id")
                request.state.user_id = payload.get("user_id")
            except Exception:
                # Protected endpoints will return the proper 401 through get_current_user.
                pass
        return await call_next(request)
