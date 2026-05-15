import pytest
from rest_framework import status


# ──────────────────────────────────────────────
# User Model
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_defaults_to_staff(self, create_user):
        user = create_user(username="newuser")
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_create_user_with_email(self, create_user):
        user = create_user(username="emailuser", email="a@b.com")
        assert user.email == "a@b.com"


# ──────────────────────────────────────────────
# Register API
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestRegisterAPI:
    def test_register_success(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {"username": "reguser", "password": "securepass123"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "user" in data
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["username"] == "reguser"

    def test_register_missing_password(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {"username": "nopass"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, api_client, create_user):
        create_user(username="dupuser")
        resp = api_client.post(
            "/api/auth/register/",
            {"username": "dupuser", "password": "anotherpass123"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────
# Login API
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestLoginAPI:
    def test_login_success(self, api_client, create_user, user_password):
        create_user(username="loginuser")
        resp = api_client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": user_password},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_wrong_password(self, api_client, create_user):
        create_user(username="wrongpw")
        resp = api_client.post(
            "/api/auth/login/",
            {"username": "wrongpw", "password": "badpassword"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, create_user, user_password):
        create_user(username="refreshuser")
        login_resp = api_client.post(
            "/api/auth/login/",
            {"username": "refreshuser", "password": user_password},
            format="json",
        )
        refresh_token = login_resp.json()["refresh"]

        resp = api_client.post(
            "/api/auth/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.json()


# ──────────────────────────────────────────────
# Me API
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestMeAPI:
    def test_me_authenticated(self, api_client, create_user, user_password):
        user = create_user(username="meuser")
        login_resp = api_client.post(
            "/api/auth/login/",
            {"username": "meuser", "password": user_password},
            format="json",
        )
        access = login_resp.json()["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["username"] == "meuser"

    def test_me_unauthenticated(self, api_client):
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
