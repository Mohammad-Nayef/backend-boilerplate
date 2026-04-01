from sqlalchemy.orm import Session
from app.infrastructure.tables.user import UserTable
from app.infrastructure.sql_helpers import execute_raw_query, bulk_insert
from app.common.constants import QueryResult

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email_orm(self, email: str) -> UserTable | None:
        """Example using standard SQLAlchemy ORM."""
        return self.db.query(UserTable).filter(UserTable.email == email).first()

    def get_by_id_raw(self, user_id: int) -> dict | None:
        """Example using raw SQL helper."""
        query_sql = "SELECT id, email, role, is_active FROM users WHERE id = :user_id"
        return execute_raw_query(
            self.db, 
            query_sql, 
            returns=QueryResult.DICT, 
            user_id=user_id
        )

    def create(self, user: UserTable) -> UserTable:
        """Example using generic bulk_insert helper for ORM models."""
        bulk_insert(self.db, user) # Uses the helper internally
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_active_users_raw(self) -> list[dict]:
        """Example using raw SQL helper to return a list of dicts."""
        query_sql = "SELECT id, email FROM users WHERE is_active = :is_active"
        return execute_raw_query(
            self.db, 
            query_sql, 
            returns=QueryResult.LIST_OF_DICT, 
            is_active=True
        )
