import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestConversationAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "aiuser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_conversation(self):
        resp = self.client.post("/api/ai/conversations/", {"title": "测试对话"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["title"] == "测试对话"

    def test_list_conversations(self):
        self.client.post("/api/ai/conversations/", {"title": "对话1"}, format="json")
        self.client.post("/api/ai/conversations/", {"title": "对话2"}, format="json")
        resp = self.client.get("/api/ai/conversations/", format="json")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_delete_conversation(self):
        conv = self.client.post("/api/ai/conversations/", {"title": "删除我"}, format="json")
        conv_id = conv.json()["id"]
        resp = self.client.delete(f"/api/ai/conversations/{conv_id}/", format="json")
        assert resp.status_code == 204


@pytest.mark.django_db
class TestPromptTemplateAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "templateuser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_template(self):
        resp = self.client.post(
            "/api/ai/templates/",
            {"name": "代码审查", "prompt": "请审查{语言}代码", "variables": ["语言"], "category": "dev"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "代码审查"

    def test_list_templates(self):
        self.client.post("/api/ai/templates/", {"name": "T1", "prompt": "p1", "variables": [], "category": "a"}, format="json")
        resp = self.client.get("/api/ai/templates/", format="json")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


@pytest.mark.django_db
class TestModuleListAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "moduser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_list_modules(self):
        resp = self.client.get("/api/modules/", format="json")
        assert resp.status_code == 200
        # 应至少包含 demo 模块
        names = [m["name"] for m in resp.json()]
        assert "demo" in names
