import pytest
from fastapi.testclient import TestClient
from app.tables.user import UserTable
from app.core.security import get_password_hash

def test_register_user_success(client: TestClient):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert "id" in data

def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "strongpassword123"
    }
    client.post("/api/auth/register", json=payload)
    
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"

def test_login_success(client: TestClient, db_session):
    # Pre-seed a user
    user = UserTable(
        email="login@example.com", 
        hashed_password=get_password_hash("mypassword")
    )
    db_session.add(user)
    db_session.commit()
    
    payload = {
        "email": "login@example.com",
        "password": "mypassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    
    # Check if the HttpOnly secure cookie was set
    cookies = response.cookies
    assert "token" in cookies

def test_login_invalid_password(client: TestClient, db_session):
    user = UserTable(
        email="wrong@example.com", 
        hashed_password=get_password_hash("correctpassword")
    )
    db_session.add(user)
    db_session.commit()
    
    payload = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401

def test_logout(client: TestClient):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    
    # Ensure cookie was deleted (Max-Age or Expire header indicates removal)
    cookie_header = response.headers.get("set-cookie")
    assert 'token=""' in cookie_header or "Max-Age=0" in cookie_header or "expires" in cookie_header.lower()
