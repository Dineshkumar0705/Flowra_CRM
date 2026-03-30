"""
Flowra database engine, session factory, and base model.

We use synchronous SQLAlchemy 2.0 with psycopg2 (the only PostgreSQL
driver available in the current environment).  FastAPI runs sync route
handlers in a thread pool automatically, so this is safe and production-
viable.  When asyncpg becomes available, the swap to AsyncSession is a
single-file change.

Usage in routes (via deps.py):
    def my_endpoint(db: Session = Depends(get_db)):
        ...
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

log = logging.getLogger("flowra.database")

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,          # recycle connections every 30 min
    pool_pre_ping=True,         # detect stale connections
    echo=False,                 # never log raw SQL in production
    future=True,                # SQLAlchemy 2.0 style
)


@event.listens_for(engine, "connect")
def set_postgres_search_path(dbapi_connection, connection_record):
    """Force UTC timezone on every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET timezone = 'UTC'")
    cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,     # objects remain usable after commit
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for use in FastAPI dependency injection.

    The session is always closed — even if an exception is raised.

    Example:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Context-manager helper (for non-FastAPI usage, e.g. scripts, tests)
# ---------------------------------------------------------------------------

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context-manager wrapper around a database session.

    Example:
        with db_session() as db:
            user = db.query(User).first()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_db_connection() -> bool:
    """
    Verify the database is reachable.

    Returns True on success, False on failure.
    Never raises — safe to call in health-check endpoints.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        log.error("database.health_check.failed", error=str(exc))
        return False


# ---------------------------------------------------------------------------
# Dev-mode helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables that are registered on Base.metadata.

    ⚠️  Use Alembic migrations in staging and production.
        This function is only for development convenience.
    """
    import app.models  # noqa: F401 — side-effect: registers all models
    Base.metadata.create_all(bind=engine)
    log.info("database.tables_created")


def drop_db() -> None:
    """
    Drop all tables.

    ⚠️  Destroys data.  Development use only.
    """
    Base.metadata.drop_all(bind=engine)
    log.warning("database.tables_dropped")
