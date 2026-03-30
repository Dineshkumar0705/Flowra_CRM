"""
Alembic environment — wired to Flowra's SQLAlchemy models.

Run migrations:
    alembic revision --autogenerate -m "your message"
    alembic upgrade head
    alembic downgrade -1
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool, text
from alembic import context

# ---------------------------------------------------------------------------
# Make sure `app` package is importable regardless of working directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent   # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Load Flowra settings (reads DATABASE_URL from .env or environment)
# ---------------------------------------------------------------------------
from app.core.config import settings

# ---------------------------------------------------------------------------
# Import ALL models so Alembic autogenerate can detect them
# ---------------------------------------------------------------------------
from app.core.database import Base  # noqa: F401  — registers DeclarativeBase

# Import in FK-dependency order so autogenerate detects foreign keys correctly
import app.models.user                  # noqa: F401
import app.models.workspace             # noqa: F401
import app.models.contact               # noqa: F401
import app.models.deal                  # noqa: F401
import app.models.pipeline              # noqa: F401
import app.models.whatsapp_message      # noqa: F401
import app.models.gmail_integration     # noqa: F401
import app.models.billing               # noqa: F401
import app.models.notification          # noqa: F401
import app.models.calendar_integration  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url from application settings (ignores alembic.ini value)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def include_schemas(names):
    """Only include the public schema (skip alembic internal schemas)."""
    return True


def run_migrations_offline() -> None:
    """
    Offline mode — generate SQL without a live DB connection.
    Useful for reviewing migrations before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online mode — connect to a live DB and apply migrations.
    Used by `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enforce UTC for this migration session
        connection.execute(text("SET timezone = 'UTC'"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
