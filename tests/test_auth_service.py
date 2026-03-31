import pytest
from unittest.mock import MagicMock
from app.services.auth_service import AuthService
from app.models.auth import UserRegisterDto
from app.core.exceptions import ConflictException
from app.tables.user import UserTable

def test_auth_service_registration_logic():
    """Unit test for business logic using pure mocks (no database)."""
    # 1. Setup Mock Repository
    mock_repo = MagicMock()
    
    # Simulate: User already exists
    mock_repo.get_by_email_orm.return_value = UserTable(email="exists@test.com")
    
    auth_service = AuthService(user_repo=mock_repo)

    # 2. Test Conflict Exception
    req = UserRegisterDto(email="exists@test.com", password="password123")
    with pytest.raises(ConflictException):
        auth_service.register_user(req)

    # 3. Test Successful Path
    mock_repo.get_by_email_orm.return_value = None # Email is free
    mock_repo.create.side_effect = lambda user: user # Just return the user passed in
    
    clean_req = UserRegisterDto(email="new@test.com", password="password123")
    result = auth_service.register_user(clean_req)
    
    assert result.email == "new@test.com"
    # Verify the service actually called the repo's create methods
    mock_repo.create.assert_called_once()
