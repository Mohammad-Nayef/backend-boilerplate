from app.tables.user import UserTable

def test_independence_part_1(db_session):
    """Insert a specific user in the first test."""
    user = UserTable(
        email="test_isolation@example.com",
        hashed_password="hashed_password",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify the user is there
    found = db_session.query(UserTable).filter_by(email="test_isolation@example.com").first()
    assert found is not None

def test_independence_part_2(db_session):
    """The second test should have a completely clean slate."""
    # This query MUST return None if isolation/rollback is working
    found = db_session.query(UserTable).filter_by(email="test_isolation@example.com").first()
    assert found is None, "Isolation failed: Data leaked from previous test!"
