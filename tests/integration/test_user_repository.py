import pytest
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.tables.user import UserTable

@pytest.mark.integration
def test_create_and_get_user_orm(db_session):
    repo = UserRepository(db_session)
    user = UserTable(email="test@example.com", hashed_password="hashedpassword123", role="admin")
    
    # Test ORM bulk_insert utility wrapper
    created_user = repo.create(user)
    assert created_user.id is not None
    assert created_user.email == "test@example.com"
    
    # Test ORM retrieval
    fetched_user = repo.get_by_email_orm("test@example.com")
    assert fetched_user is not None
    assert fetched_user.role == "admin"

@pytest.mark.integration
def test_get_by_id_raw(db_session):
    repo = UserRepository(db_session)
    user = UserTable(email="raw@example.com", hashed_password="123", role="user")
    repo.create(user)
    
    # Test raw SQL execution mapping to dictionary
    raw_user = repo.get_by_id_raw(user.id)
    assert raw_user is not None
    assert isinstance(raw_user, dict)
    assert raw_user["email"] == "raw@example.com"
    assert raw_user["role"] == "user"

@pytest.mark.integration
def test_get_all_active_users_raw(db_session):
    repo = UserRepository(db_session)
    user1 = UserTable(email="active1@example.com", hashed_password="123", is_active=True)
    user2 = UserTable(email="active2@example.com", hashed_password="123", is_active=True)
    user3 = UserTable(email="inactive@example.com", hashed_password="123", is_active=False)
    
    repo.create(user1)
    repo.create(user2)
    repo.create(user3)
    
    active_users = repo.get_all_active_users_raw()
    assert len(active_users) == 2
    emails = [u["email"] for u in active_users]
    assert "active1@example.com" in emails
    assert "active2@example.com" in emails
    assert "inactive@example.com" not in emails
