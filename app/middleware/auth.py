from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User

class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.url.path.startswith("/api/routes/auth"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header.split(" ")[1]

        db = SessionLocal()
        try:
            payload = decode_token(token)
            user = db.query(User).filter(User.id == payload["user_id"]).first()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid user")

            request.state.user = user

        finally:
            db.close()

        return await call_next(request)