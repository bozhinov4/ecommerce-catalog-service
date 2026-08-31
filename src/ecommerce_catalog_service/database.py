"""Database engine, base model, and session dependency."""

from collections.abc import Generator
from datetime import datetime
from functools import lru_cache
from typing import ClassVar

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ecommerce_catalog_service.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    type_annotation_map: ClassVar = {datetime: DateTime(timezone=True)}


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the process-wide database session factory."""
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session]:
    """Yield a database session for one request."""
    with get_session_factory()() as session:
        yield session
