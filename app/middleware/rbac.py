from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException

class RBACMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        user = getattr(request.state, "user", None)

        if user:
            permissions = [rp.permission.name for rp in user.role.role_permissions]
            request.state.permissions = permissions

        return await call_next(request)