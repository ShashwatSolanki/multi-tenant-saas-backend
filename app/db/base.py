from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata
# Import all models so they are registered with SQLAlchemy metadata
from app.models.organization import Organization  # noqa
from app.models.user import User  # noqa
from app.models.role import Role  # noqa
from app.models.permission import Permission  # noqa
from app.models.role_permission import RolePermission  # noqa
from app.models.business_resource import BusinessResource  # noqa
