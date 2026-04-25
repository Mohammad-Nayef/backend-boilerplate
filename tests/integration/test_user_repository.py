import pytest

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.tables.user import UserTable


@pytest.mark.integration
def test_create_and_get_user_by_email(db_session):
    repo = UserRepository(db_session)
    user = UserTable(
        full_name="Test User",
        email="test@example.com",
        password_salt="salt",
        hashed_password="hashedpassword123",
        is_active=False,
    )

    created_user = repo.create(user)
    assert created_user.id is not None
    assert created_user.email == "test@example.com"
    assert created_user.created_by == created_user.id
    assert created_user.updated_by == created_user.id

    fetched_user = repo.get_by_email("test@example.com")
    assert fetched_user is not None
    assert fetched_user.full_name == "Test User"


@pytest.mark.integration
def test_get_by_id_raw(db_session):
    repo = UserRepository(db_session)
    user = UserTable(
        full_name="Raw User",
        email="raw@example.com",
        password_salt="salt",
        hashed_password="123",
        is_active=True,
    )
    created = repo.create(user)

    raw_user = repo.get_by_id_raw(created.id)
    assert raw_user is not None
    assert isinstance(raw_user, dict)
    assert raw_user["email"] == "raw@example.com"
    assert raw_user["is_active"] is True


@pytest.mark.integration
def test_save_updates_user_record(db_session):
    repo = UserRepository(db_session)
    user = UserTable(
        full_name="Before Update",
        email="update@example.com",
        password_salt="salt",
        hashed_password="hash",
        is_active=False,
    )
    created = repo.create(user)

    created.full_name = "After Update"
    created.is_active = True
    updated = repo.save(created)

    assert updated.full_name == "After Update"
    assert updated.is_active is True


@pytest.mark.integration
def test_get_all_active_users_raw(db_session):
    repo = UserRepository(db_session)
    repo.create(
        UserTable(
            full_name="Active One",
            email="active1@example.com",
            password_salt="salt",
            hashed_password="123",
            is_active=True,
        )
    )
    repo.create(
        UserTable(
            full_name="Active Two",
            email="active2@example.com",
            password_salt="salt",
            hashed_password="123",
            is_active=True,
        )
    )
    repo.create(
        UserTable(
            full_name="Inactive",
            email="inactive@example.com",
            password_salt="salt",
            hashed_password="123",
            is_active=False,
        )
    )

    active_users = repo.get_all_active_users_raw()
    assert len(active_users) == 2
    emails = {user["email"] for user in active_users}
    assert "active1@example.com" in emails
    assert "active2@example.com" in emails
    assert "inactive@example.com" not in emails
