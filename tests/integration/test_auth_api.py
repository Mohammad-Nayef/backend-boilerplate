import pytest
from fastapi.testclient import TestClient
from app.infrastructure.tables.user import UserTable
from app.infrastructure.security import get_password_hash

@pytest.mark.integration
def test_register_user_success(client: TestClient, mock_email_service):
    """Integration test: Real DB, mocking internal email utility."""
    payload = {
        "email": "integration@test.com",
        "password": "stongpassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    
    assert response.status_code == 200
    # Verification: Database side-effect
    data = response.json()
    assert data["email"] == "integration@test.com"

@pytest.mark.integration
def test_login_and_state_management(client: TestClient, db_session):
    """Integration test: Stateful sessions using DB persistence."""
    # 1. Seed DB
    user = UserTable(
        email="session@example.com", 
        hashed_password=get_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    
    # 2. Login
    payload = {"email": "session@example.com", "password": "password"}
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 200
    assert "token" in response.cookies

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "session@example.com"
    assert me_response.json()["role"] == "user"
    
    # 3. Logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    after_logout = client.get("/api/auth/me")
    assert after_logout.status_code == 401


@pytest.mark.integration
def test_protected_auth_route_rejects_inactive_users(
    client: TestClient,
    db_session,
):
    user = UserTable(
        email="inactive@example.com",
        hashed_password=get_password_hash("password"),
    )
    db_session.add(user)
    db_session.commit()

    login_response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "password"},
    )
    assert login_response.status_code == 200

    persisted_user = db_session.query(UserTable).filter_by(email="inactive@example.com").one()
    persisted_user.is_active = False
    db_session.commit()

    response = client.get("/api/auth/me")

    assert response.status_code == 401
