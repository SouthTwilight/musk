import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db(databases="__all__")
class TestCategoryModel(TestCase):
    databases = "__all__"

    def test_create_category(self):
        from apps.blog.models import Category
        cat = Category.objects.create(
            name="技术",
            icon="💻",
            score_thresholds={"low": [1, 3], "mid": [4, 6], "high": [7, 10]},
        )
        assert cat.name == "技术"
        assert cat.score_thresholds["high"] == [7, 10]

    def test_category_unique_name(self):
        from apps.blog.models import Category
        from django.db import IntegrityError
        Category.objects.create(name="AI", icon="🤖")
        with pytest.raises(IntegrityError):
            Category.objects.create(name="AI", icon="🤖")


@pytest.mark.django_db(databases="__all__")
class TestArticleModel(TestCase):
    databases = "__all__"

    def test_create_article(self):
        from apps.blog.models import Article, Category
        cat = Category.objects.create(name="技术", icon="💻")
        article = Article.objects.create(
            title="测试文章",
            url="https://example.com/test",
            category=cat,
            source_name="Example",
            status="pending",
        )
        assert article.title == "测试文章"
        assert article.status == "pending"

    def test_article_url_unique(self):
        from apps.blog.models import Article
        from django.db import IntegrityError
        Article.objects.create(title="A1", url="https://example.com/1", source_name="S")
        with pytest.raises(IntegrityError):
            Article.objects.create(title="A2", url="https://example.com/1", source_name="S")


@pytest.mark.django_db(databases="__all__")
class TestRSSSourceModel(TestCase):
    databases = "__all__"

    def test_create_rss_source(self):
        from apps.blog.models import RSSSource, Category
        cat = Category.objects.create(name="技术", icon="💻")
        source = RSSSource.objects.create(
            name="TechCrunch",
            url="https://techcrunch.com/feed/",
            category=cat,
            fetch_interval=3600,
        )
        assert source.name == "TechCrunch"
        assert source.is_active is True


@pytest.mark.django_db(databases="__all__")
class TestBlogConfig(TestCase):
    databases = "__all__"

    def test_create_config(self):
        from apps.blog.models import BlogConfig
        cfg = BlogConfig.objects.create(
            key="l1_model",
            value="deepseek-chat",
        )
        assert cfg.key == "l1_model"


@pytest.mark.django_db(databases="__all__")
class TestFailedURL(TestCase):
    databases = "__all__"

    def test_create_failed_url(self):
        from apps.blog.models import FailedURL
        f = FailedURL.objects.create(url="https://example.com/404", reason="404")
        assert f.reason == "404"


@pytest.mark.django_db(databases="__all__")
class TestScoreDimension(TestCase):
    databases = "__all__"

    def test_create_dimension(self):
        from apps.blog.models import ScoreDimension
        d = ScoreDimension.objects.create(name="技术深度", description="文章技术含量")
        assert d.name == "技术深度"


# ── API 测试 ──


def _register_client(test_id):
    """注册用户并返回已认证的 APIClient。"""
    client = APIClient()
    reg = client.post(
        "/api/auth/register/",
        {"username": f"blogapi_{test_id}", "password": "testpass123"},
        format="json",
    )
    token = reg.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db(databases="__all__")
class TestCategoryAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_list_categories_empty(self):
        resp = self.client.get("/api/blog/categories/", format="json")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_list_category(self):
        resp = self.client.post(
            "/api/blog/categories/",
            {"name": "技术", "icon": "💻", "score_thresholds": {"low": [1, 3], "mid": [4, 6], "high": [7, 10]}},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "技术"

        resp = self.client.get("/api/blog/categories/", format="json")
        assert len(resp.json()) == 1

    def test_update_category(self):
        cat = self.client.post(
            "/api/blog/categories/",
            {"name": "AI", "icon": "🤖", "score_thresholds": {"low": [1, 3], "mid": [4, 6], "high": [7, 10]}},
            format="json",
        )
        cat_id = cat.json()["id"]
        resp = self.client.put(
            f"/api/blog/categories/{cat_id}/",
            {"name": "AI", "icon": "🤖", "score_thresholds": {"low": [1, 4], "mid": [5, 6], "high": [7, 10]}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["score_thresholds"]["low"] == [1, 4]


@pytest.mark.django_db(databases="__all__")
class TestRSSSourceAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_create_rss_source(self):
        resp = self.client.post(
            "/api/blog/rss-sources/",
            {"name": "HackerNews", "url": "https://hnrss.org/frontpage", "fetch_interval": 3600},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "HackerNews"

    def test_list_rss_sources(self):
        self.client.post(
            "/api/blog/rss-sources/",
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            format="json",
        )
        resp = self.client.get("/api/blog/rss-sources/", format="json")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.django_db(databases="__all__")
class TestArticleAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_list_articles_empty(self):
        resp = self.client.get("/api/blog/articles/", format="json")
        assert resp.status_code == 200

    def test_filter_by_status(self):
        from apps.blog.models import Article
        Article.objects.create(
            title="Done Article", url="https://example.com/done",
            status="done", source_name="Test",
        )
        Article.objects.create(
            title="Pending Article", url="https://example.com/pending",
            status="pending", source_name="Test",
        )
        resp = self.client.get("/api/blog/articles/?status=done", format="json")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["title"] == "Done Article"


@pytest.mark.django_db(databases="__all__")
class TestBlogConfigAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_get_config_defaults(self):
        resp = self.client.get("/api/blog/config/", format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["l1_model"] == "deepseek-chat"
        assert data["rss_source_limit"] == 40

    def test_update_config(self):
        resp = self.client.put(
            "/api/blog/config/",
            {"l2_model": "deepseek-chat"},
            format="json",
        )
        assert resp.status_code == 200
        resp = self.client.get("/api/blog/config/", format="json")
        assert resp.json()["l2_model"] == "deepseek-chat"


@pytest.mark.django_db(databases="__all__")
class TestRSSSourceLimit(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_rss_source_limit(self):
        # 设置上限为 2
        from apps.blog.models import BlogConfig
        BlogConfig.objects.using(_get_db_helper()).update_or_create(
            key="rss_source_limit", defaults={"value": 2}
        )
        # 创建 2 个源
        self.client.post("/api/blog/rss-sources/", {"name": "S1", "url": "https://s1.com/feed"}, format="json")
        self.client.post("/api/blog/rss-sources/", {"name": "S2", "url": "https://s2.com/feed"}, format="json")
        # 第 3 个应该被拒绝
        resp = self.client.post("/api/blog/rss-sources/", {"name": "S3", "url": "https://s3.com/feed"}, format="json")
        assert resp.status_code == 400


def _get_db_helper():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


# ── Fetcher 测试 ──

from unittest.mock import patch, MagicMock


@pytest.mark.django_db(databases="__all__")
class TestFetcher:
    databases = "__all__"

    def test_fetch_article_success(self):
        from apps.blog.services.fetcher import fetch_article
        mock_html = "<html><head><title>Test</title></head><body><p>Hello world article content here.</p></body></html>"
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = mock_html
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            with patch("trafilatura.extract", return_value="Hello world article content here."):
                result = fetch_article("https://example.com/test")
                assert result["status"] == "pending"
                assert result["raw_text"] == "Hello world article content here."

    def test_fetch_article_404(self):
        from apps.blog.services.fetcher import fetch_article
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = Exception("404 Not Found")
            result = fetch_article("https://example.com/404")
            assert result["status"] == "failed"

    def test_fetch_article_unparsable(self):
        from apps.blog.services.fetcher import fetch_article
        mock_html = "<html><body></body></html>"
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = mock_html
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            with patch("trafilatura.extract", return_value=None):
                result = fetch_article("https://example.com/empty")
                assert result["status"] == "unparsable"
                assert "raw_html" in result

    def test_fetch_and_store_dedup(self):
        from apps.blog.models import Article
        from apps.blog.services.fetcher import fetch_and_store_article
        Article.objects.using(_get_db_helper()).create(
            title="Existing", url="https://example.com/existing",
            status="done", source_name="Test",
        )
        result = fetch_and_store_article("https://example.com/existing")
        assert result["status"] == "duplicate"
