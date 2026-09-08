from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.models import AuditLog, Role, User
from app.schemas import UserResponse, UserUpdate

router = APIRouter()


def response(user: User) -> dict:
    return {"user_id": user.user_id, "tenant_id": user.tenant_id, "email": user.email, "full_name": user.full_name, "role": user.role.name, "is_active": user.is_active}


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, data: UserUpdate, db: Session = Depends(get_db), actor: User = Depends(require_roles("Owner"))):
    target = db.scalar(select(User).where(User.user_id == user_id, User.tenant_id == actor.tenant_id, User.deleted_at.is_(None)))
    if not target:
        raise HTTPException(404, "User not found")
    if target.user_id == actor.user_id and (data.role is not None or data.is_active is False):
        raise HTTPException(409, "The Owner cannot remove their own Owner access")
    if target.role.name == "Owner" and data.role is not None:
        raise HTTPException(409, "Owner role cannot be reassigned")
    if data.role is not None:
        role = db.scalar(select(Role).where(Role.name == data.role))
        if not role:
            raise HTTPException(400, "Invalid role")
        target.role_id = role.role_id
    if data.full_name is not None:
        target.full_name = data.full_name
    if data.is_active is not None:
        target.is_active = data.is_active
    db.add(AuditLog(user_id=actor.user_id, action="update", entity_type="user", entity_id=target.user_id, description=f"Updated user {target.email}: role={target.role.name}, active={target.is_active}"))
    db.commit()
    db.refresh(target)
    return response(target)
