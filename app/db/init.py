from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base, engine
from app.models.models import Role

DEFAULT_ROLES = {
    "Owner": "Tenant owner with full administrative access",
    "Admin": "Tenant administrator",
    "Member": "Standard tenant member",
}


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        for name, description in DEFAULT_ROLES.items():
            if not db.scalar(select(Role).where(Role.name == name)):
                db.add(Role(name=name, role_description=description))
        db.commit()
