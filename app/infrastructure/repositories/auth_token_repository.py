from datetime import datetime, timezone
from sqlalchemy import text

from app.common.constants import AuthTokenPurpose, QueryResult
from app.infrastructure.sql_helpers import sql
from app.infrastructure.tables.auth_token import AuthTokenTable


class AuthTokenRepository:
    def __init__(self, db):
        self.db = db

    def issue_token(
        self,
        *,
        user_id: int,
        purpose: AuthTokenPurpose,
        token_hash: str,
        expires_at: datetime,
    ) -> AuthTokenTable:
        self.db.execute(
            AuthTokenTable.__table__.update()
            .where(
                AuthTokenTable.user_id == user_id,
                AuthTokenTable.purpose == purpose.value,
                AuthTokenTable.used_at.is_(None),
            )
            .values(used_at=datetime.now(timezone.utc))
        )
        token = AuthTokenTable(
            user_id=user_id,
            purpose=purpose.value,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_latest_for_user(
        self,
        *,
        user_id: int,
        purpose: AuthTokenPurpose,
    ) -> AuthTokenTable | None:
        row = sql(
            self.db,
            """
                SELECT id, user_id, purpose, token_hash, created_at, expires_at, used_at
                FROM auth_tokens
                WHERE user_id = :user_id AND purpose = :purpose
                ORDER BY created_at DESC
                LIMIT 1
            """,
            returns=QueryResult.DICT,
            user_id=user_id,
            purpose=purpose.value,
        )
        if not row:
            return None
        return AuthTokenTable(**row)

    def get_by_token_hash(
        self,
        *,
        purpose: AuthTokenPurpose,
        token_hash: str,
    ) -> AuthTokenTable | None:
        row = sql(
            self.db,
            """
                SELECT id, user_id, purpose, token_hash, created_at, expires_at, used_at
                FROM auth_tokens
                WHERE purpose = :purpose AND token_hash = :token_hash
                LIMIT 1
            """,
            returns=QueryResult.DICT,
            purpose=purpose.value,
            token_hash=token_hash,
        )
        if not row:
            return None
        return AuthTokenTable(**row)

    def consume_by_id(self, token_id: int) -> bool:
        now = datetime.now(timezone.utc)
        result = self.db.execute(
            text(
                """
                    UPDATE auth_tokens
                    SET used_at = :used_at
                    WHERE id = :token_id
                      AND used_at IS NULL
                      AND expires_at > :used_at
                """
            ),
            {"used_at": now, "token_id": token_id},
        )
        self.db.commit()
        return result.rowcount > 0
