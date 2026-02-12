import uuid
from datetime import datetime
from sqlalchemy import String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", name="organization_status"),
        nullable=False,
        default="active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, status={self.status})>"
