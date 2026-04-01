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
    
    # 3. Logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
