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
