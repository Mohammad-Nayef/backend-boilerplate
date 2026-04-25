from typing import Any

from sqlalchemy.orm import Session

from app.common.constants import QueryResult
from app.infrastructure.sql_helpers import insert, sql
from app.infrastructure.tables.user import UserTable


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _map_row_to_user(self, row: dict[str, Any]) -> UserTable:
        return UserTable(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_salt=row["password_salt"],
            hashed_password=row["hashed_password"],
            is_active=row["is_active"],
            email_verified_at=row.get("email_verified_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            created_by=row.get("created_by"),
            updated_by=row.get("updated_by"),
        )

    def get_by_email(self, email: str) -> UserTable | None:
        row = sql(
            self.db,
            """
                SELECT
                    id, full_name, email, password_salt, hashed_password, is_active,
                    email_verified_at, created_at, updated_at, created_by, updated_by
                FROM users
                WHERE LOWER(email) = :normalized_email
                LIMIT 1
            """,
            returns=QueryResult.DICT,
            normalized_email=email.strip().lower(),
        )
        if not row:
            return None
        return self._map_row_to_user(row)

    def get_by_id(self, user_id: int) -> UserTable | None:
        row = sql(
            self.db,
            """
                SELECT
                    id, full_name, email, password_salt, hashed_password, is_active,
                    email_verified_at, created_at, updated_at, created_by, updated_by
                FROM users
                WHERE id = :user_id
                LIMIT 1
            """,
            returns=QueryResult.DICT,
            user_id=user_id,
        )
        if not row:
            return None
        return self._map_row_to_user(row)

    def get_by_id_raw(self, user_id: int) -> dict | None:
        result = sql(
            self.db,
            """
                SELECT
                    id, full_name, email, is_active, email_verified_at,
                    created_at, updated_at, created_by, updated_by
                FROM users
                WHERE id = :user_id
            """,
            returns=QueryResult.DICT,
            user_id=user_id,
        )
        return result or None

    def create(self, user: UserTable) -> UserTable:
        insert(self.db, user)
        user.created_by = user.id
        user.updated_by = user.id
        self.db.commit()
        return self.get_by_id(user.id) or user

    def save(self, user: UserTable) -> UserTable:
        sql(
            self.db,
            """
                UPDATE users
                SET
                    full_name = :full_name,
                    email = :email,
                    password_salt = :password_salt,
                    hashed_password = :hashed_password,
                    is_active = :is_active,
                    email_verified_at = :email_verified_at,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = :updated_by
                WHERE id = :user_id
            """,
            full_name=user.full_name,
            email=user.email,
            password_salt=user.password_salt,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            email_verified_at=user.email_verified_at,
            updated_by=user.id,
            user_id=user.id,
        )
        self.db.commit()
        return self.get_by_id(user.id) or user

    def get_all_active_users_raw(self) -> list[dict]:
        return sql(
            self.db,
            "SELECT id, email FROM users WHERE is_active = :is_active",
            returns=QueryResult.LIST_OF_DICT,
            is_active=True,
        )
