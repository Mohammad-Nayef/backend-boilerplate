import pytest
from app.infrastructure.tables.user import UserTable


@pytest.mark.integration
def test_independence_part_1(db_session):
    user = UserTable(
        full_name="Isolation User",
        email="test_isolation@example.com",
        password_salt="salt",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    found = (
        db_session.query(UserTable)
        .filter_by(email="test_isolation@example.com")
        .first()
    )
    assert found is not None


@pytest.mark.integration
def test_independence_part_2(db_session):
    found = (
        db_session.query(UserTable)
        .filter_by(email="test_isolation@example.com")
        .first()
    )
    assert found is None, "Isolation failed: data leaked from previous test"
