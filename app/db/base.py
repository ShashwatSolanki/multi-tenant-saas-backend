from sqlalchemy import create_engine

from app.core.config import settings
from app.models.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)
