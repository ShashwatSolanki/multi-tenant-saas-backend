from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.models import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    payload = decode_access_token(authorization.split(" ", 1)[1])
    try:
        user_id = UUID(payload["user_id"])
        tenant_id = UUID(payload["tenant_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token claims") from exc

    user = db.scalar(select(User).where(User.user_id == user_id, User.tenant_id == tenant_id, User.deleted_at.is_(None), User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=401, detail="User is inactive or no longer exists")

    # The database is authoritative for the user's current role and tenant.
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker
