import pytest
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.dtos.auth import UserRegisterDto
from app.core.exceptions import ConflictException

class MockUserRepository:
    def __init__(self):
        self.users = {}
        self.counter = 1

    def get_by_email_orm(self, email):
        return self.users.get(email)

    def create(self, user):
        user.id = self.counter
        self.counter += 1
        self.users[user.email] = user
        return user

def test_auth_service_register_user_business_logic():
    mock_repo = MockUserRepository()
    
    # Python doesn't strict check types unless enforced, so we can pass the Mock
    auth_service = AuthService(user_repo=mock_repo) # type: ignore
    
    # 1. Successful registration
    req = UserRegisterDto(email="service@test.com", password="password")
    new_user = auth_service.register_user(req)
    
    assert new_user.id == 1
    assert new_user.email == "service@test.com"
    assert new_user.hashed_password != "password" # Must be hashed

    # 2. Conflict on duplicate email
    with pytest.raises(ConflictException) as exc:
        auth_service.register_user(req)
    
    assert str(exc.value.detail) == "Email already exists"
