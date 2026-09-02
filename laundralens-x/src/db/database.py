"""
LaundraLens X — SQLAlchemy database engine and session management.
Uses SQLite for the hackathon prototype (configurable via DATABASE_URL).
"""
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from config.settings import settings


# Ensure data directory exists
Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False,
)

# Enable WAL mode for SQLite performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """Create all tables defined in ORM models."""
    # Import models to register them with Base
    from src.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
