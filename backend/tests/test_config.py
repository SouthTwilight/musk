import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestConfigAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "configuser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_default_config(self):
        resp = self.client.get("/api/config/", format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] == "dark"
        assert data["sidebar_collapsed"] is False

    def test_update_theme(self):
        resp = self.client.patch("/api/config/", {"theme": "light"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["theme"] == "light"

    def test_update_sidebar(self):
        resp = self.client.patch("/api/config/", {"sidebar_collapsed": True}, format="json")
        assert resp.status_code == 200
        assert resp.json()["sidebar_collapsed"] is True


@pytest.mark.django_db
class TestStorageAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "storageuser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_list_files_empty(self):
        resp = self.client.get("/api/storage/", format="json")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_upload_file(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        resp = self.client.post("/api/storage/", {"file": file}, format="multipart")
        assert resp.status_code == 201
        assert resp.json()["filename"] == "test.txt"
