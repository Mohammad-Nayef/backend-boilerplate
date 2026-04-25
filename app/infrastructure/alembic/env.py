import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool, text

from app.infrastructure.base import Base
import app.infrastructure.tables  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _get_database_url() -> str:
    configured_url = config.get_main_option("sqlalchemy.url")
    if configured_url:
        return configured_url

    for env_var_name in ("DB_URL", "DATABASE_URL"):
        env_url = os.getenv(env_var_name)
        if env_url:
            return env_url

    from app.common.config import settings

    return settings.DB_URL


target_metadata = Base.metadata


def _ensure_version_table_supports_long_revision_ids(connection) -> None:
    inspector = inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        connection.execute(
            text(
                """
                CREATE TABLE alembic_version (
                    version_num VARCHAR(64) NOT NULL PRIMARY KEY
                )
                """
            )
        )
        connection.commit()
        return

    connection.execute(
        text(
            """
            ALTER TABLE alembic_version
            ALTER COLUMN version_num TYPE VARCHAR(64)
            """
        )
    )
    connection.commit()


def run_migrations_offline() -> None:
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_database_url().replace("%", "%%")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _ensure_version_table_supports_long_revision_ids(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
