from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        user = getattr(request.state, "user", None)

        if user:
            request.state.org_id = user.organization_id

        return await call_next(request)