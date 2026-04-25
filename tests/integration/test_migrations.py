import os
import sys

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, inspect, text
from testcontainers.postgres import PostgresContainer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

ALEMBIC_INI_PATH = os.path.join(PROJECT_ROOT, "alembic.ini")


def _build_alembic_config(database_url: str) -> Config:
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return alembic_cfg


@pytest.mark.migration
def test_alembic_upgrade_applies_head_schema():
    with PostgresContainer("postgres:15", dbname="migration_test_db") as postgres:
        database_url = postgres.get_connection_url(driver="pg8000")
        alembic_cfg = _build_alembic_config(database_url)
        expected_head = ScriptDirectory.from_config(alembic_cfg).get_current_head()

        command.upgrade(alembic_cfg, "head")

        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                applied_head = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()

            table_names = set(inspect(engine).get_table_names())
            user_columns = {
                column["name"] for column in inspect(engine).get_columns("users")
            }
            auth_token_columns = {
                column["name"] for column in inspect(engine).get_columns("auth_tokens")
            }
        finally:
            engine.dispose()

    assert applied_head == expected_head
    assert "users" in table_names
    assert "auth_tokens" in table_names
    assert {"full_name", "email", "password_salt", "hashed_password"} <= user_columns
    assert {"purpose", "token_hash", "expires_at", "used_at"} <= auth_token_columns
