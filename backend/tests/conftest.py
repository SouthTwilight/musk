import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_password():
    return "testpass123456"


@pytest.fixture
def create_user(db, user_password):
    from core.auth.models import User

    def _create_user(username="testuser", password=None, **kwargs):
        user = User(username=username, **kwargs)
        user.set_password(password or user_password)
        user.save()
        return user

    return _create_user
