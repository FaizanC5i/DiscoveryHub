"""
Alembic environment: tells migrations which database to change and which models to compare.

Analogy: the site foreman's briefing. It names the building (the Azure SQL
database, read from .env) and the blueprint (our ORM models) before any work
order runs.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Used by "alembic revision --autogenerate" to compare models with the database.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to a file without connecting (alembic upgrade --sql)."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to Azure SQL and apply the migrations."""
    # NullPool: migrations are short-lived scripts, so do not keep a pool open.
    engine = create_engine(get_settings().database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
