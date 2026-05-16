# 博客引擎模块实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现 blog 模块——RSS/URL 文章抓取、二级 AI 过滤、笔记展示与 MD 导出。

**架构：** 标准 Musk 模块结构（backend/apps/blog/ + frontend/src/views/blog/），独立 SQLite 数据库，通过 FrameworkAPI 访问 AI 适配器，APScheduler 定时抓取，前端 1:2 分栏详情页。

**技术栈：** Django 4.2 + DRF + feedparser + trafilatura + httpx + APScheduler | Vue 3 + Pinia + vue-router

---

## 文件结构

### 后端（创建）

| 文件 | 职责 |
|------|------|
| `backend/apps/blog/__init__.py` | 空，Python 包 |
| `backend/apps/blog/manifest.py` | 模块注册元数据 |
| `backend/apps/blog/apps.py` | Django AppConfig，启动 APScheduler |
| `backend/apps/blog/models.py` | 6 张数据表定义 |
| `backend/apps/blog/serializers.py` | DRF 序列化器 |
| `backend/apps/blog/views.py` | API 视图 |
| `backend/apps/blog/urls.py` | URL 路由 |
| `backend/apps/blog/services/__init__.py` | 空 |
| `backend/apps/blog/services/fetcher.py` | RSS/URL 内容抓取 |
| `backend/apps/blog/services/processor.py` | AI 二级处理流水线 |
| `backend/apps/blog/services/exporter.py` | MD 文件导出 |
| `backend/apps/blog/scheduler.py` | APScheduler 定时任务 |
| `backend/tests/test_blog.py` | 模块测试 |

### 后端（修改）

| 文件 | 变更 |
|------|------|
| `backend/requirements.txt` | 添加 feedparser、trafilatura、httpx、apscheduler |

### 前端（创建）

| 文件 | 职责 |
|------|------|
| `frontend/src/stores/blog.ts` | 博客 Pinia store |
| `frontend/src/views/blog/BlogListView.vue` | 列表页 |
| `frontend/src/views/blog/ArticleDetailView.vue` | 详情页 |
| `frontend/src/views/blog/settings/BlogSettingsView.vue` | 设置页 |
| `frontend/src/views/blog/AddUrlDialog.vue` | URL 弹窗 |

### 前端（修改）

| 文件 | 变更 |
|------|------|
| `frontend/src/router/index.ts` | 添加 /blog 路由 |

---

## 任务 1：模块骨架 + 数据模型

**文件：**
- 创建：`backend/apps/blog/__init__.py`
- 创建：`backend/apps/blog/manifest.py`
- 创建：`backend/apps/blog/apps.py`
- 创建：`backend/apps/blog/models.py`
- 修改：`backend/requirements.txt`
- 测试：`backend/tests/test_blog.py`

- [ ] **步骤 1：添加依赖到 requirements.txt**

在 `backend/requirements.txt` 末尾追加：

```
feedparser>=6.0.*
trafilatura>=1.8.*
httpx>=0.27.*
apscheduler>=3.10.*
```

- [ ] **步骤 2：安装依赖**

运行：`cd E:\WSL\musk\backend && pip install feedparser trafilatura httpx apscheduler`

- [ ] **步骤 3：创建模块骨架文件**

`backend/apps/blog/__init__.py` — 空文件

`backend/apps/blog/manifest.py`：
```python
MANIFEST = {
    "name": "blog",
    "version": "1.0.0",
    "display_name": "知识笔记",
    "icon": "📚",
    "description": "RSS/URL 文章抓取 + AI 二级过滤 + 深度笔记",
    "menu_order": 5,
}
```

`backend/apps/blog/apps.py`：
```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
    label = "apps_blog"
    verbose_name = "知识笔记"

    def ready(self):
        # 仅在主进程启动调度器（避免 migrate 等命令重复启动）
        import os
        if os.environ.get("RUN_MAIN") == "true" or not os.environ.get("RUN_MAIN"):
            # 首次 ready 时不启动，通过 management 命令或手动触发
            pass
```

- [ ] **步骤 4：编写失败测试 — 数据模型**

创建 `backend/tests/test_blog.py`：
```python
import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestCategoryModel(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "bloguser", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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


@pytest.mark.django_db
class TestArticleModel(TestCase):
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


@pytest.mark.django_db
class TestRSSSourceModel(TestCase):
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


@pytest.mark.django_db
class TestBlogConfig(TestCase):
    def test_create_config(self):
        from apps.blog.models import BlogConfig
        cfg = BlogConfig.objects.create(
            key="l1_model",
            value="deepseek-chat",
        )
        assert cfg.key == "l1_model"


@pytest.mark.django_db
class TestFailedURL(TestCase):
    def test_create_failed_url(self):
        from apps.blog.models import FailedURL
        f = FailedURL.objects.create(url="https://example.com/404", reason="404")
        assert f.reason == "404"


@pytest.mark.django_db
class TestScoreDimension(TestCase):
    def test_create_dimension(self):
        from apps.blog.models import ScoreDimension
        d = ScoreDimension.objects.create(name="技术深度", description="文章技术含量")
        assert d.name == "技术深度"
```

- [ ] **步骤 5：运行测试验证失败**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py -v`
预期：FAIL — `ModuleNotFoundError: No module named 'apps.blog'`

- [ ] **步骤 6：创建 models.py**

`backend/apps/blog/models.py`：
```python
import uuid
from django.db import models


class Category(models.Model):
    """文章分类。"""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, default="📁")
    score_thresholds = models.JSONField(
        default=dict,
        help_text='分档范围，如 {"low": [1,3], "mid": [4,6], "high": [7,10]}',
    )
    article_count = models.IntegerField(default=0)

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_category"
        ordering = ["name"]

    def __str__(self):
        return self.name


class RSSSource(models.Model):
    """RSS 订阅源。"""
    name = models.CharField(max_length=200)
    url = models.URLField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    fetch_interval = models.IntegerField(
        default=3600, help_text="抓取间隔（秒）"
    )
    last_fetched = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_rss_source"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Article(models.Model):
    """文章。"""
    STATUS_CHOICES = [
        ("pending", "待处理"),
        ("processing", "处理中"),
        ("done", "已完成"),
        ("failed", "获取失败"),
        ("unparsable", "无法解析"),
    ]

    title = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    source = models.ForeignKey(
        RSSSource, on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    score = models.IntegerField(null=True, blank=True)
    source_name = models.CharField(max_length=200, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    # AI 生成内容
    summary = models.TextField(blank=True, default="")
    key_points = models.TextField(blank=True, default="")
    deep_analysis = models.TextField(blank=True, default="")
    # 原文缓存
    raw_html = models.TextField(blank=True, default="")
    raw_text = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_article"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class FailedURL(models.Model):
    """获取失败的 URL 记录。"""
    url = models.URLField(unique=True)
    reason = models.CharField(max_length=200)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_failed_url"
        ordering = ["-attempted_at"]


class BlogConfig(models.Model):
    """博客模块配置。"""
    key = models.CharField(max_length=50, unique=True)
    value = models.JSONField()

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_config"

    def __str__(self):
        return self.key


class ScoreDimension(models.Model):
    """评分维度。"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    weight = models.FloatField(default=1.0)

    class Meta:
        app_label = "apps_blog"
        db_table = "blog_score_dimension"
        ordering = ["name"]

    def __str__(self):
        return self.name
```

- [ ] **步骤 7：创建 migrations 目录**

运行：`mkdir -p E:\WSL\musk\backend\apps\blog\migrations && touch E:\WSL\musk\backend\apps\blog\migrations\__init__.py`

- [ ] **步骤 8：运行迁移**

运行：`cd E:\WSL\musk\backend && python manage.py makemigrations apps_blog && python manage.py migrate`

- [ ] **步骤 9：运行测试验证通过**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py -v`
预期：全部 PASS

- [ ] **步骤 10：Commit**

```bash
cd E:\WSL\musk
git add backend/apps/blog/ backend/requirements.txt backend/tests/test_blog.py
git commit -m "feat(blog): 添加博客模块骨架 + 6 张数据模型"
```

---

## 任务 2：序列化器 + API 视图 + URL 路由

**文件：**
- 创建：`backend/apps/blog/serializers.py`
- 创建：`backend/apps/blog/views.py`
- 创建：`backend/apps/blog/urls.py`
- 修改：`backend/tests/test_blog.py`（追加 API 测试）

- [ ] **步骤 1：编写失败测试 — API 端点**

追加到 `backend/tests/test_blog.py`：
```python
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCategoryAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": f"bloguser_{self.id()}", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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


@pytest.mark.django_db
class TestRSSSourceAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": f"rssuser_{self.id()}", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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


@pytest.mark.django_db
class TestArticleAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": f"artuser_{self.id()}", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py::TestCategoryAPI -v`
预期：FAIL — 404（URL 不存在）

- [ ] **步骤 3：创建 serializers.py**

`backend/apps/blog/serializers.py`：
```python
from rest_framework import serializers
from apps.blog.models import (
    Category, RSSSource, Article, FailedURL, BlogConfig, ScoreDimension,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "icon", "score_thresholds", "article_count")
        read_only_fields = ("id", "article_count")


class RSSSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSSSource
        fields = (
            "id", "name", "url", "category", "fetch_interval",
            "last_fetched", "is_active", "created_at",
        )
        read_only_fields = ("id", "last_fetched", "created_at")


class ArticleListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", default="")
    category_icon = serializers.CharField(source="category.icon", default="")

    class Meta:
        model = Article
        fields = (
            "id", "title", "url", "category", "category_name", "category_icon",
            "status", "score", "source_name", "summary",
            "published_at", "created_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + (
            "key_points", "deep_analysis", "raw_text",
        )


class FailedURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailedURL
        fields = ("id", "url", "reason", "attempted_at")
        read_only_fields = ("id", "attempted_at")


class BlogConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogConfig
        fields = ("id", "key", "value")
        read_only_fields = ("id",)


class ScoreDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreDimension
        fields = ("id", "name", "description", "weight")
        read_only_fields = ("id",)


class FetchURLSerializer(serializers.Serializer):
    url = serializers.URLField()
    category_id = serializers.IntegerField(required=False, allow_null=True)
```

- [ ] **步骤 4：创建 views.py**

`backend/apps/blog/views.py`：
```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
import io

from apps.blog.models import (
    Category, RSSSource, Article, FailedURL, BlogConfig, ScoreDimension,
)
from apps.blog.serializers import (
    CategorySerializer, RSSSourceSerializer,
    ArticleListSerializer, ArticleDetailSerializer,
    FailedURLSerializer, BlogConfigSerializer, ScoreDimensionSerializer,
    FetchURLSerializer,
)
from apps.blog.services.exporter import export_article_md


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=_get_db())


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.using(_get_db()).all()


class RSSSourceListCreateView(generics.ListCreateAPIView):
    serializer_class = RSSSourceSerializer

    def get_queryset(self):
        return RSSSource.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        # 检查上限
        current_count = RSSSource.objects.using(_get_db()).count()
        limit_cfg = BlogConfig.objects.using(_get_db()).filter(key="rss_source_limit").first()
        limit = limit_cfg.value if limit_cfg else 40
        if current_count >= limit:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"RSS 源已达上限 {limit} 个")
        serializer.save(using=_get_db())


class RSSSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RSSSourceSerializer

    def get_queryset(self):
        return RSSSource.objects.using(_get_db()).all()


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer

    def get_queryset(self):
        qs = Article.objects.using(_get_db()).all()
        category = self.request.query_params.get("category")
        status_filter = self.request.query_params.get("status")
        score_min = self.request.query_params.get("score_min")
        if category:
            qs = qs.filter(category_id=category)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if score_min:
            qs = qs.filter(score__gte=int(score_min))
        return qs


class ArticleDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ArticleDetailSerializer

    def get_queryset(self):
        return Article.objects.using(_get_db()).all()


class FetchURLView(APIView):
    """手动粘贴 URL 抓取文章。"""

    def post(self, request):
        serializer = FetchURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]
        category_id = serializer.validated_data.get("category_id")

        from apps.blog.services.fetcher import fetch_and_store_article
        result = fetch_and_store_article(url, category_id=category_id)
        return Response(result, status=status.HTTP_201_CREATED)


class ArticleExportView(APIView):
    """导出单篇文章为 MD。"""

    def post(self, request, pk):
        article = Article.objects.using(_get_db()).get(pk=pk)
        md_content = export_article_md(article)
        buf = io.BytesIO(md_content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f"{article.title[:50]}.md",
            content_type="text/markdown",
        )


class ArticleReprocessView(APIView):
    """重新 AI 处理文章。"""

    def post(self, request, pk):
        article = Article.objects.using(_get_db()).get(pk=pk)
        from apps.blog.services.processor import process_article
        process_article(article)
        return Response({"status": "done"})


class FailedURLListView(generics.ListAPIView):
    serializer_class = FailedURLSerializer

    def get_queryset(self):
        return FailedURL.objects.using(_get_db()).all()


class FailedURLDetailView(generics.DestroyAPIView):
    serializer_class = FailedURLSerializer

    def get_queryset(self):
        return FailedURL.objects.using(_get_db()).all()


class BlogConfigView(APIView):
    """获取/更新博客配置。"""

    def get(self, request):
        configs = BlogConfig.objects.using(_get_db()).all()
        data = {c.key: c.value for c in configs}
        # 补充默认值
        defaults = {
            "l1_model": "deepseek-chat",
            "l2_model": "glm-4-plus",
            "rss_source_limit": 40,
            "default_score_dims": ["技术深度", "时效性", "实用价值", "创新性"],
        }
        for k, v in defaults.items():
            data.setdefault(k, v)
        return Response(data)

    def put(self, request):
        for key, value in request.data.items():
            BlogConfig.objects.using(_get_db()).update_or_create(
                key=key, defaults={"value": value}
            )
        return Response({"detail": "配置已更新"})


class SchedulerStatusView(APIView):
    """调度状态。"""

    def get(self, request):
        from apscheduler.schedulers.background import BackgroundScheduler
        # 返回各源的下次抓取时间
        sources = RSSSource.objects.using(_get_db()).filter(is_active=True)
        jobs = []
        for s in sources:
            jobs.append({
                "source_id": s.id,
                "name": s.name,
                "interval": s.fetch_interval,
                "last_fetched": s.last_fetched,
            })
        return Response({"jobs": jobs})


class FetchAllView(APIView):
    """手动触发全量抓取。"""

    def post(self, request):
        from apps.blog.services.fetcher import fetch_all_sources
        count = fetch_all_sources()
        return Response({"detail": f"已处理 {count} 篇新文章"})


class ScoreDimensionListCreateView(generics.ListCreateAPIView):
    serializer_class = ScoreDimensionSerializer

    def get_queryset(self):
        return ScoreDimension.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=_get_db())


class ScoreDimensionDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ScoreDimensionSerializer

    def get_queryset(self):
        return ScoreDimension.objects.using(_get_db()).all()


class BatchExportView(APIView):
    """批量导出。"""

    def post(self, request):
        article_ids = request.data.get("article_ids", [])
        category_id = request.data.get("category_id")

        qs = Article.objects.using(_get_db()).all()
        if article_ids:
            qs = qs.filter(id__in=article_ids)
        elif category_id:
            qs = qs.filter(category_id=category_id)

        parts = []
        for article in qs:
            parts.append(export_article_md(article))
            parts.append("\n\n---\n\n")

        content = "".join(parts)
        buf = io.BytesIO(content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename="articles_export.md",
            content_type="text/markdown",
        )
```

- [ ] **步骤 5：创建 urls.py**

`backend/apps/blog/urls.py`：
```python
from django.urls import path
from apps.blog.views import (
    CategoryListCreateView, CategoryDetailView,
    RSSSourceListCreateView, RSSSourceDetailView,
    ArticleListView, ArticleDetailView,
    FetchURLView, ArticleExportView, ArticleReprocessView,
    FailedURLListView, FailedURLDetailView,
    BlogConfigView, SchedulerStatusView, FetchAllView,
    ScoreDimensionListCreateView, ScoreDimensionDetailView,
    BatchExportView,
)

urlpatterns = [
    # 分类
    path("categories/", CategoryListCreateView.as_view(), name="blog-categories"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="blog-category-detail"),
    # RSS 源
    path("rss-sources/", RSSSourceListCreateView.as_view(), name="blog-rss-sources"),
    path("rss-sources/<int:pk>/", RSSSourceDetailView.as_view(), name="blog-rss-source-detail"),
    # 文章
    path("articles/", ArticleListView.as_view(), name="blog-articles"),
    path("articles/fetch_url/", FetchURLView.as_view(), name="blog-fetch-url"),
    path("articles/export_batch/", BatchExportView.as_view(), name="blog-export-batch"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="blog-article-detail"),
    path("articles/<int:pk>/export/", ArticleExportView.as_view(), name="blog-article-export"),
    path("articles/<int:pk>/reprocess/", ArticleReprocessView.as_view(), name="blog-article-reprocess"),
    # 无效链接
    path("failed-urls/", FailedURLListView.as_view(), name="blog-failed-urls"),
    path("failed-urls/<int:pk>/", FailedURLDetailView.as_view(), name="blog-failed-url-detail"),
    # 配置
    path("config/", BlogConfigView.as_view(), name="blog-config"),
    path("config/dimensions/", ScoreDimensionListCreateView.as_view(), name="blog-score-dimensions"),
    path("config/dimensions/<int:pk>/", ScoreDimensionDetailView.as_view(), name="blog-score-dimension-detail"),
    # 调度
    path("scheduler/status/", SchedulerStatusView.as_view(), name="blog-scheduler-status"),
    path("scheduler/fetch_all/", FetchAllView.as_view(), name="blog-fetch-all"),
]
```

- [ ] **步骤 6：创建 services 占位文件**

`backend/apps/blog/services/__init__.py` — 空文件

`backend/apps/blog/services/fetcher.py`（占位，任务 3 完善）：
```python
def fetch_and_store_article(url: str, category_id=None) -> dict:
    return {"status": "pending", "title": "", "url": url}


def fetch_all_sources() -> int:
    return 0
```

`backend/apps/blog/services/processor.py`（占位，任务 4 完善）：
```python
def process_article(article):
    article.status = "done"
    article.save(using=_get_db())
```

`backend/apps/blog/services/exporter.py`（占位，任务 5 完善）：
```python
def export_article_md(article) -> str:
    return f"# {article.title}"
```

- [ ] **步骤 7：运行测试验证通过**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py -v`
预期：全部 PASS

- [ ] **步骤 8：Commit**

```bash
cd E:\WSL\musk
git add backend/apps/blog/
git commit -m "feat(blog): 添加 API 视图 + 序列化器 + URL 路由"
```

---

## 任务 3：抓取服务（fetcher.py）

**文件：**
- 修改：`backend/apps/blog/services/fetcher.py`
- 修改：`backend/tests/test_blog.py`（追加 fetcher 测试）

- [ ] **步骤 1：编写失败测试 — fetcher**

追加到 `backend/tests/test_blog.py`：
```python
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestFetcher(TestCase):
    def test_fetch_article_success(self):
        from apps.blog.services.fetcher import fetch_article
        mock_html = "<html><body><p>Hello world article content here.</p></body></html>"
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
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body></body></html>"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            with patch("trafilatura.extract", return_value=None):
                result = fetch_article("https://example.com/empty")
                assert result["status"] == "unparsable"
                assert "raw_html" in result

    def test_fetch_and_store_dedup(self):
        from apps.blog.models import Article, FailedURL
        from apps.blog.services.fetcher import fetch_and_store_article
        Article.objects.create(
            title="Existing", url="https://example.com/existing",
            status="done", source_name="Test",
        )
        result = fetch_and_store_article("https://example.com/existing")
        assert result["status"] == "duplicate"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py::TestFetcher -v`
预期：FAIL

- [ ] **步骤 3：实现 fetcher.py**

`backend/apps/blog/services/fetcher.py`：
```python
"""RSS/URL 内容抓取服务。"""

import logging
from datetime import datetime

import httpx
import trafilatura
import feedparser

from apps.blog.models import Article, RSSSource, FailedURL

logger = logging.getLogger(__name__)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


def fetch_article(url: str) -> dict:
    """抓取单篇文章，返回结果字典。"""
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Fetch failed for %s: %s", url, e)
        return {"status": "failed", "reason": str(e)[:200]}

    html = resp.text

    # 尝试用 trafilatura 提取正文
    try:
        text = trafilatura.extract(html)
    except Exception:
        text = None

    if not text:
        return {
            "status": "unparsable",
            "raw_html": html,
            "title": _extract_title(html),
            "url": url,
        }

    metadata = trafilatura.extract(html, output_format="json")
    title = _extract_title(html)
    published_at = None
    if metadata:
        import json
        try:
            meta = json.loads(metadata)
            title = meta.get("title", title)
        except Exception:
            pass

    return {
        "status": "pending",
        "title": title or url,
        "url": url,
        "raw_html": html,
        "raw_text": text,
        "published_at": published_at,
        "source_name": _extract_source_name(url),
    }


def fetch_and_store_article(url: str, category_id=None) -> dict:
    """抓取单篇文章并存入数据库。"""
    db = _get_db()

    # URL 去重
    if Article.objects.using(db).filter(url=url).exists():
        return {"status": "duplicate", "url": url}
    if FailedURL.objects.using(db).filter(url=url).exists():
        return {"status": "duplicate_failed", "url": url}

    result = fetch_article(url)

    if result["status"] == "failed":
        FailedURL.objects.using(db).create(
            url=url, reason=result.get("reason", "unknown"),
        )
        return result

    # 获取分类
    from apps.blog.models import Category
    category = None
    if category_id:
        try:
            category = Category.objects.using(db).get(pk=category_id)
        except Category.DoesNotExist:
            pass

    article = Article.objects.using(db).create(
        title=result.get("title", url),
        url=url,
        status=result["status"],
        raw_html=result.get("raw_html", ""),
        raw_text=result.get("raw_text", ""),
        source_name=result.get("source_name", ""),
        published_at=result.get("published_at"),
        category=category,
    )

    # 如果提取成功，触发 AI 处理
    if article.status == "pending" and article.raw_text:
        from apps.blog.services.processor import process_article
        process_article(article)

    return {
        "status": article.status,
        "title": article.title,
        "url": article.url,
        "id": article.id,
        "score": article.score,
    }


def fetch_rss_source(source: RSSSource) -> int:
    """抓取单个 RSS 源，返回新增文章数。"""
    db = _get_db()
    new_count = 0

    try:
        feed = feedparser.parse(source.url)
    except Exception as e:
        logger.error("RSS parse failed for %s: %s", source.name, e)
        return 0

    for entry in feed.entries:
        url = entry.get("link")
        if not url:
            continue

        # 去重
        if Article.objects.using(db).filter(url=url).exists():
            continue
        if FailedURL.objects.using(db).filter(url=url).exists():
            continue

        result = fetch_article(url)

        if result["status"] == "failed":
            FailedURL.objects.using(db).create(
                url=url, reason=result.get("reason", "unknown"),
            )
            continue

        article = Article.objects.using(db).create(
            title=result.get("title", entry.get("title", url)),
            url=url,
            source=source,
            category=source.category,
            status=result["status"],
            raw_html=result.get("raw_html", ""),
            raw_text=result.get("raw_text", ""),
            source_name=source.name,
            published_at=_parse_published(entry),
        )

        if article.status == "pending" and article.raw_text:
            from apps.blog.services.processor import process_article
            process_article(article)

        new_count += 1

    # 更新抓取时间
    source.last_fetched = datetime.now()
    source.save(using=db)

    return new_count


def fetch_all_sources() -> int:
    """抓取所有活跃 RSS 源，返回总新增文章数。"""
    db = _get_db()
    total = 0
    for source in RSSSource.objects.using(db).filter(is_active=True):
        try:
            total += fetch_rss_source(source)
        except Exception as e:
            logger.error("Error fetching source %s: %s", source.name, e)
    return total


def _extract_title(html: str) -> str:
    """从 HTML 中提取 title。"""
    import re
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_source_name(url: str) -> str:
    """从 URL 提取域名作为来源名。"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "")


def _parse_published(entry) -> datetime | None:
    """从 feed entry 解析发布时间。"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        from time import mktime
        return datetime.fromtimestamp(mktime(entry.published_parsed))
    return None
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py::TestFetcher -v`
预期：全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd E:\WSL\musk
git add backend/apps/blog/services/fetcher.py backend/tests/test_blog.py
git commit -m "feat(blog): 实现内容抓取服务 (RSS + URL)"
```

---

## 任务 4：AI 处理流水线（processor.py）

**文件：**
- 修改：`backend/apps/blog/services/processor.py`
- 修改：`backend/tests/test_blog.py`（追加 processor 测试）

- [ ] **步骤 1：编写失败测试 — processor**

追加到 `backend/tests/test_blog.py`：
```python
@pytest.mark.django_db
class TestProcessor(TestCase):
    def test_process_article_low_score(self):
        from apps.blog.models import Article, Category
        from apps.blog.services.processor import process_article
        cat = Category.objects.create(
            name="TestCat", icon="T",
            score_thresholds={"low": [1, 3], "mid": [4, 6], "high": [7, 10]},
        )
        article = Article.objects.create(
            title="Low Score", url="https://example.com/low",
            category=cat, source_name="Test", status="pending",
            raw_text="Some article text",
        )
        with patch("apps.blog.services.processor._call_ai") as mock_ai:
            mock_ai.return_value = '{"score": 2}'
            # L1 returns score 2, then summary
            mock_ai.side_effect = ['{"score": 2, "tags": []}', "Short summary"]
            process_article(article)
        article.refresh_from_db()
        assert article.score == 2
        assert article.status == "done"
        assert article.summary != ""

    def test_process_article_high_score(self):
        from apps.blog.models import Article, Category
        from apps.blog.services.processor import process_article
        cat = Category.objects.create(
            name="HighCat", icon="H",
            score_thresholds={"low": [1, 3], "mid": [4, 6], "high": [7, 10]},
        )
        article = Article.objects.create(
            title="High Score", url="https://example.com/high",
            category=cat, source_name="Test", status="pending",
            raw_text="Excellent deep technical article",
        )
        with patch("apps.blog.services.processor._call_ai") as mock_ai:
            mock_ai.side_effect = [
                '{"score": 9, "tags": ["AI"]}',  # L1 score
                "Summary text",                  # summary
                '["Point 1", "Point 2"]',        # key_points
                "Deep analysis content",          # deep_analysis
            ]
            process_article(article)
        article.refresh_from_db()
        assert article.score == 9
        assert article.deep_analysis != ""

    def test_process_article_no_category(self):
        from apps.blog.models import Article
        from apps.blog.services.processor import process_article
        article = Article.objects.create(
            title="No Cat", url="https://example.com/nocat",
            source_name="Test", status="pending",
            raw_text="Some text",
        )
        with patch("apps.blog.services.processor._call_ai") as mock_ai:
            mock_ai.side_effect = ['{"score": 5}', "Summary"]
            process_article(article)
        article.refresh_from_db()
        assert article.status == "done"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py::TestProcessor -v`
预期：FAIL

- [ ] **步骤 3：实现 processor.py**

`backend/apps/blog/services/processor.py`：
```python
"""AI 二级处理流水线。"""

import json
import logging

from apps.blog.models import Article, BlogConfig, ScoreDimension

logger = logging.getLogger(__name__)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


def _call_ai(messages: list, model_name: str = None) -> str:
    """调用 AI 模型，返回文本响应。"""
    from core.ai.adapters import get_adapter
    adapter = get_adapter(model_name)
    return adapter.chat(messages, stream=False)


def _get_config(key: str, default=None):
    db = _get_db()
    cfg = BlogConfig.objects.using(db).filter(key=key).first()
    return cfg.value if cfg else default


def _get_default_thresholds() -> dict:
    return {"low": [1, 3], "mid": [4, 6], "high": [7, 10]}


def _get_score_dimensions() -> list[str]:
    db = _get_db()
    dims = list(ScoreDimension.objects.using(db).values_list("name", flat=True))
    if not dims:
        dims = _get_config("default_score_dims", ["技术深度", "时效性", "实用价值", "创新性"])
    return dims


def process_article(article: Article):
    """处理单篇文章的 AI 流水线。"""
    db = _get_db()
    article.status = "processing"
    article.save(using=db)

    try:
        thresholds = (
            article.category.score_thresholds
            if article.category
            else _get_default_thresholds()
        )

        # ── L1：便宜模型打分 ──
        l1_model = _get_config("l1_model", "deepseek")
        dims = _get_score_dimensions()
        dims_text = "、".join(dims)

        l1_prompt = f"""请对以下文章内容进行评分（1-10分），考虑以下维度：{dims_text}。
仅返回 JSON 格式：{{"score": N, "tags": ["标签1", "标签2"]}}"""

        l1_response = _call_ai(
            [
                {"role": "system", "content": l1_prompt},
                {"role": "user", "content": article.raw_text[:3000]},
            ],
            model_name=l1_model,
        )

        score_data = _parse_json(l1_response)
        article.score = score_data.get("score", 5)

        # ── 根据分档决定处理深度 ──
        if article.score <= thresholds["low"][1]:
            # 低分：仅总结
            article.summary = _generate_summary(
                article.raw_text[:2000], l1_model
            )
        elif article.score <= thresholds["mid"][1]:
            # 中分：总结 + 要点
            l2_model = _get_config("l2_model", "glm")
            article.summary = _generate_summary(article.raw_text, l2_model)
            article.key_points = _generate_key_points(article.raw_text, l2_model)
        else:
            # 高分：全套
            l2_model = _get_config("l2_model", "glm")
            article.summary = _generate_summary(article.raw_text, l2_model)
            article.key_points = _generate_key_points(article.raw_text, l2_model)
            article.deep_analysis = _generate_deep_analysis(article.raw_text, l2_model)

        article.status = "done"

    except Exception as e:
        logger.error("AI processing failed for article %s: %s", article.id, e)
        article.status = "done"  # 即使 AI 失败也标记完成，保留原文
        article.summary = f"AI 处理失败: {str(e)[:100]}"

    article.save(using=db)


def _generate_summary(text: str, model: str) -> str:
    return _call_ai(
        [
            {"role": "system", "content": "请用中文总结以下文章内容，200字以内。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )


def _generate_key_points(text: str, model: str) -> str:
    result = _call_ai(
        [
            {"role": "system", "content": "请提取以下文章的关键要点，以 JSON 数组格式返回，每项不超过30字。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )
    return result


def _generate_deep_analysis(text: str, model: str) -> str:
    return _call_ai(
        [
            {"role": "system", "content": "请对以下文章进行深度分析，包括：核心观点、技术细节、潜在影响、实践建议。500字以内。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )


def _parse_json(text: str) -> dict:
    """从 AI 响应中解析 JSON。"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 块
    import re
    match = re.search(r"\{[^}]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"score": 5}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py::TestProcessor -v`
预期：全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd E:\WSL\musk
git add backend/apps/blog/services/processor.py backend/tests/test_blog.py
git commit -m "feat(blog): 实现 AI 二级处理流水线"
```

---

## 任务 5：导出 + 调度服务

**文件：**
- 修改：`backend/apps/blog/services/exporter.py`
- 创建：`backend/apps/blog/scheduler.py`
- 修改：`backend/apps/blog/apps.py`（启动调度器）

- [ ] **步骤 1：实现 exporter.py**

`backend/apps/blog/services/exporter.py`：
```python
"""MD 文件导出服务。"""

import json


def export_article_md(article) -> str:
    """导出单篇文章为 Markdown（不含原文）。"""
    # 格式化要点
    points_text = ""
    if article.key_points:
        try:
            points = json.loads(article.key_points)
            if isinstance(points, list):
                points_text = "\n".join(f"- {p}" for p in points)
            else:
                points_text = str(points)
        except (json.JSONDecodeError, TypeError):
            points_text = article.key_points

    md = f"""# {article.title}

> Source: [{article.source_name}]({article.url}) | Level: {article.score or 'N/A'}/10

## Summary
{article.summary or '_无总结_'}

## Key Points
{points_text or '_无要点_'}

## DeepAnalysis
{article.deep_analysis or '_未进行深度分析_'}
"""
    return md
```

- [ ] **步骤 2：创建 scheduler.py**

`backend/apps/blog/scheduler.py`：
```python
"""APScheduler 定时任务管理。"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler():
    """启动调度器，注册所有活跃 RSS 源的定时任务。"""
    sched = get_scheduler()

    try:
        from apps.blog.models import RSSSource

        def _get_db():
            from module_layer.registry import registry
            info = registry.get("blog")
            return info.db_alias if info else "default"

        for source in RSSSource.objects.using(_get_db()).filter(is_active=True):
            _add_source_job(sched, source)
    except Exception as e:
        logger.warning("Failed to register RSS jobs: %s", e)

    if not sched.running:
        sched.start()
        logger.info("Blog scheduler started")


def _add_source_job(sched, source):
    """注册单个 RSS 源的定时抓取任务。"""
    from apps.blog.services.fetcher import fetch_rss_source

    def _job(source_id):
        try:
            from apps.blog.models import RSSSource

            db = _get_db()
            src = RSSSource.objects.using(db).get(pk=source_id)
            count = fetch_rss_source(src)
            if count:
                logger.info("Fetched %d new articles from %s", count, src.name)
        except Exception as e:
            logger.error("Scheduled fetch failed for source %s: %s", source_id, e)

    sched.add_job(
        _job,
        "interval",
        seconds=source.fetch_interval,
        args=[source.id],
        id=f"rss_{source.id}",
        replace_existing=True,
    )


def refresh_jobs():
    """刷新所有定时任务（RSS 源变更后调用）。"""
    sched = get_scheduler()
    # 移除所有 rss_ 开头的 job
    for job in sched.get_jobs():
        if job.id.startswith("rss_"):
            sched.remove_job(job.id)
    # 重新注册
    try:
        from apps.blog.models import RSSSource

        def _get_db():
            from module_layer.registry import registry
            info = registry.get("blog")
            return info.db_alias if info else "default"

        for source in RSSSource.objects.using(_get_db()).filter(is_active=True):
            _add_source_job(sched, source)
    except Exception as e:
        logger.warning("Failed to refresh RSS jobs: %s", e)
```

- [ ] **步骤 3：更新 apps.py 启动调度器**

`backend/apps/blog/apps.py`：
```python
import os
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
    label = "apps_blog"
    verbose_name = "知识笔记"

    def ready(self):
        # 仅在 runserver 主进程或 gunicorn worker 中启动调度器
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("START_SCHEDULER") == "1":
            try:
                from apps.blog.scheduler import start_scheduler
                start_scheduler()
            except Exception:
                pass  # 避免 migrate 等命令出错
```

- [ ] **步骤 4：运行全量测试**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py -v`
预期：全部 PASS

- [ ] **步骤 5：Commit**

```bash
cd E:\WSL\musk
git add backend/apps/blog/services/exporter.py backend/apps/blog/scheduler.py backend/apps/blog/apps.py
git commit -m "feat(blog): 实现 MD 导出 + APScheduler 定时抓取"
```

---

## 任务 6：初始化默认数据 + RSS 源上限校验测试

**文件：**
- 修改：`backend/tests/test_blog.py`（追加默认配置 + 上限测试）

- [ ] **步骤 1：编写默认配置初始化 + RSS 上限测试**

追加到 `backend/tests/test_blog.py`：
```python
@pytest.mark.django_db
class TestBlogConfigAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": f"cfguser_{self.id()}", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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


@pytest.mark.django_db
class TestRSSSourceLimit(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": f"limituser_{self.id()}", "password": "testpass123"},
            format="json",
        )
        self.token = reg.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

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
```

- [ ] **步骤 2：运行测试验证通过**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/test_blog.py -v`
预期：全部 PASS

- [ ] **步骤 3：Commit**

```bash
cd E:\WSL\musk
git add backend/tests/test_blog.py
git commit -m "test(blog): 添加配置 API + RSS 上限测试"
```

---

## 任务 7：前端 Pinia Store

**文件：**
- 创建：`frontend/src/stores/blog.ts`

- [ ] **步骤 1：创建 blog store**

`frontend/src/stores/blog.ts`：
```typescript
import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

export interface Category {
  id: number;
  name: string;
  icon: string;
  score_thresholds: { low: number[]; mid: number[]; high: number[] };
  article_count: number;
}

export interface RSSSource {
  id: number;
  name: string;
  url: string;
  category: number | null;
  fetch_interval: number;
  last_fetched: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Article {
  id: number;
  title: string;
  url: string;
  category: number | null;
  category_name: string;
  category_icon: string;
  status: string;
  score: number | null;
  source_name: string;
  summary: string;
  key_points: string;
  deep_analysis: string;
  raw_text: string;
  published_at: string | null;
  created_at: string;
}

export interface BlogConfig {
  l1_model: string;
  l2_model: string;
  rss_source_limit: number;
  default_score_dims: string[];
  [key: string]: unknown;
}

export const useBlogStore = defineStore("blog", () => {
  const categories = ref<Category[]>([]);
  const rssSources = ref<RSSSource[]>([]);
  const articles = ref<Article[]>([]);
  const currentArticle = ref<Article | null>(null);
  const config = ref<BlogConfig | null>(null);
  const loading = ref(false);
  const failedUrls = ref<{ id: number; url: string; reason: string }[]>([]);

  // ── 分类 ──
  async function fetchCategories() {
    const { data } = await api.get("/blog/categories/");
    categories.value = data;
  }

  async function createCategory(payload: Partial<Category>) {
    const { data } = await api.post("/blog/categories/", payload);
    categories.value.push(data);
    return data;
  }

  async function updateCategory(id: number, payload: Partial<Category>) {
    const { data } = await api.put(`/blog/categories/${id}/`, payload);
    const idx = categories.value.findIndex((c) => c.id === id);
    if (idx !== -1) categories.value[idx] = data;
    return data;
  }

  async function deleteCategory(id: number) {
    await api.delete(`/blog/categories/${id}/`);
    categories.value = categories.value.filter((c) => c.id !== id);
  }

  // ── RSS 源 ──
  async function fetchRSSSources() {
    const { data } = await api.get("/blog/rss-sources/");
    rssSources.value = data;
  }

  async function createRSSSource(payload: Partial<RSSSource>) {
    const { data } = await api.post("/blog/rss-sources/", payload);
    rssSources.value.push(data);
    return data;
  }

  async function updateRSSSource(id: number, payload: Partial<RSSSource>) {
    const { data } = await api.put(`/blog/rss-sources/${id}/`, payload);
    const idx = rssSources.value.findIndex((s) => s.id === id);
    if (idx !== -1) rssSources.value[idx] = data;
    return data;
  }

  async function deleteRSSSource(id: number) {
    await api.delete(`/blog/rss-sources/${id}/`);
    rssSources.value = rssSources.value.filter((s) => s.id !== id);
  }

  // ── 文章 ──
  async function fetchArticles(params?: Record<string, string>) {
    loading.value = true;
    try {
      const { data } = await api.get("/blog/articles/", { params });
      articles.value = data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchArticle(id: number) {
    const { data } = await api.get(`/blog/articles/${id}/`);
    currentArticle.value = data;
    return data;
  }

  async function fetchUrl(url: string, categoryId?: number) {
    const { data } = await api.post("/blog/articles/fetch_url/", {
      url,
      category_id: categoryId,
    });
    return data;
  }

  async function reprocessArticle(id: number) {
    const { data } = await api.post(`/blog/articles/${id}/reprocess/`);
    return data;
  }

  async function deleteArticle(id: number) {
    await api.delete(`/blog/articles/${id}/`);
    articles.value = articles.value.filter((a) => a.id !== id);
  }

  async function exportArticle(id: number) {
    const { data } = await api.post(
      `/blog/articles/${id}/export/`,
      {},
      { responseType: "blob" }
    );
    return data;
  }

  // ── 配置 ──
  async function fetchConfig() {
    const { data } = await api.get("/blog/config/");
    config.value = data;
    return data;
  }

  async function updateConfig(payload: Record<string, unknown>) {
    const { data } = await api.put("/blog/config/", payload);
    return data;
  }

  // ── 无效链接 ──
  async function fetchFailedUrls() {
    const { data } = await api.get("/blog/failed-urls/");
    failedUrls.value = data;
  }

  async function deleteFailedUrl(id: number) {
    await api.delete(`/blog/failed-urls/${id}/`);
    failedUrls.value = failedUrls.value.filter((f) => f.id !== id);
  }

  // ── 调度 ──
  async function fetchAll() {
    const { data } = await api.post("/blog/scheduler/fetch_all/");
    return data;
  }

  return {
    categories, rssSources, articles, currentArticle,
    config, loading, failedUrls,
    fetchCategories, createCategory, updateCategory, deleteCategory,
    fetchRSSSources, createRSSSource, updateRSSSource, deleteRSSSource,
    fetchArticles, fetchArticle, fetchUrl, reprocessArticle,
    deleteArticle, exportArticle,
    fetchConfig, updateConfig,
    fetchFailedUrls, deleteFailedUrl,
    fetchAll,
  };
});
```

- [ ] **步骤 2：Commit**

```bash
cd E:\WSL\musk
git add frontend/src/stores/blog.ts
git commit -m "feat(blog): 添加前端 Pinia store"
```

---

## 任务 8：前端列表页 + 详情页 + 设置页

**文件：**
- 创建：`frontend/src/views/blog/BlogListView.vue`
- 创建：`frontend/src/views/blog/ArticleDetailView.vue`
- 创建：`frontend/src/views/blog/settings/BlogSettingsView.vue`
- 创建：`frontend/src/views/blog/AddUrlDialog.vue`
- 修改：`frontend/src/router/index.ts`

- [ ] **步骤 1：创建 AddUrlDialog.vue**

`frontend/src/views/blog/AddUrlDialog.vue` — 手动粘贴 URL 的弹窗组件：
```vue
<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>添加文章链接</h3>
      <input
        v-model="url"
        class="dialog-input"
        placeholder="https://example.com/article"
        @keydown.enter="handleFetch"
      />
      <select v-model="categoryId" class="dialog-select">
        <option :value="undefined">自动分类</option>
        <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">
          {{ cat.icon }} {{ cat.name }}
        </option>
      </select>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="dialog-actions">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-primary" @click="handleFetch" :disabled="!url.trim() || fetching">
          {{ fetching ? '抓取中...' : '抓取' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useBlogStore } from "@/stores/blog";

defineProps<{ visible: boolean }>();
const emit = defineEmits<{ close: []; fetched: [] }>();

const blogStore = useBlogStore();
const url = ref("");
const categoryId = ref<number | undefined>(undefined);
const fetching = ref(false);
const error = ref("");

async function handleFetch() {
  if (!url.value.trim()) return;
  fetching.value = true;
  error.value = "";
  try {
    await blogStore.fetchUrl(url.value.trim(), categoryId.value);
    url.value = "";
    emit("fetched");
    emit("close");
  } catch (e: any) {
    error.value = e.response?.data?.detail || "抓取失败";
  } finally {
    fetching.value = false;
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg); padding: 24px; width: 480px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; color: var(--text-primary); }
.dialog-input, .dialog-select {
  width: 100%; padding: 10px 12px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 14px; margin-bottom: 12px;
}
.dialog-input:focus, .dialog-select:focus { border-color: var(--input-focus-border); outline: none; }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer;
}
.btn-primary {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: var(--error); font-size: 13px; }
</style>
```

- [ ] **步骤 2：创建 BlogListView.vue**

`frontend/src/views/blog/BlogListView.vue`：
```vue
<template>
  <div class="blog-list">
    <div class="list-header">
      <h1>知识笔记</h1>
      <button class="add-btn" @click="showAddUrl = true">+ 添加链接</button>
    </div>

    <div class="filter-bar">
      <button
        :class="['filter-chip', { active: activeFilter === 'all' }]"
        @click="setFilter('all')"
      >全部</button>
      <button
        v-for="cat in blogStore.categories"
        :key="cat.id"
        :class="['filter-chip', { active: activeFilter === String(cat.id) }]"
        @click="setFilter(String(cat.id))"
      >{{ cat.icon }} {{ cat.name }}</button>
      <button
        :class="['filter-chip high-value', { active: activeFilter === 'high' }]"
        @click="setFilter('high')"
      >⭐ 7+ 高价值</button>
    </div>

    <div v-if="blogStore.loading" class="loading">加载中...</div>
    <div v-else-if="blogStore.articles.length === 0" class="empty">
      <p>暂无文章</p>
      <p class="empty-hint">添加 RSS 源或手动粘贴 URL 开始</p>
    </div>
    <div v-else class="waterfall">
      <div
        v-for="article in blogStore.articles"
        :key="article.id"
        :class="['article-card', { 'low-score': article.score && article.score <= 3 }]"
        @click="goDetail(article.id)"
      >
        <div class="card-header">
          <span class="card-meta">{{ article.category_icon }} {{ article.category_name }}</span>
          <span v-if="article.score" class="card-score" :class="scoreClass(article.score)">
            ⭐ {{ article.score }}
          </span>
        </div>
        <h3 class="card-title">{{ article.title }}</h3>
        <p class="card-summary">{{ article.summary?.slice(0, 80) || '暂无总结' }}</p>
        <div class="card-footer">
          <span class="card-source">{{ article.source_name }}</span>
          <span class="card-date">{{ formatDate(article.created_at) }}</span>
        </div>
      </div>
    </div>

    <AddUrlDialog :visible="showAddUrl" @close="showAddUrl = false" @fetched="onFetched" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useBlogStore } from "@/stores/blog";
import AddUrlDialog from "./AddUrlDialog.vue";

const router = useRouter();
const blogStore = useBlogStore();
const activeFilter = ref("all");
const showAddUrl = ref(false);

onMounted(async () => {
  await Promise.all([
    blogStore.fetchCategories(),
    blogStore.fetchArticles(),
  ]);
});

function setFilter(filter: string) {
  activeFilter.value = filter;
  if (filter === "all") {
    blogStore.fetchArticles();
  } else if (filter === "high") {
    blogStore.fetchArticles({ score_min: "7" });
  } else {
    blogStore.fetchArticles({ category: filter });
  }
}

function goDetail(id: number) {
  router.push(`/blog/${id}`);
}

function onFetched() {
  blogStore.fetchArticles();
}

function scoreClass(score: number) {
  if (score >= 7) return "score-high";
  if (score >= 4) return "score-mid";
  return "score-low";
}

function formatDate(dateStr: string) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}
</script>

<style scoped>
.blog-list { padding: 0 0 24px; }
.list-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.list-header h1 { font-size: 24px; color: var(--text-primary); }
.add-btn {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text);
  cursor: pointer; font-size: 13px;
}
.filter-bar { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-chip {
  padding: 6px 14px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: 20px; color: var(--text-secondary); cursor: pointer;
  font-size: 13px; transition: all 0.15s;
}
.filter-chip.active {
  background: var(--accent-muted); border-color: var(--accent);
  color: var(--accent);
}
.filter-chip.high-value.active {
  background: rgba(188, 140, 255, 0.15); border-color: #bc8cff; color: #bc8cff;
}
.waterfall {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.article-card {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 16px; cursor: pointer;
  transition: all 0.2s;
}
.article-card:hover {
  border-color: var(--accent); transform: translateY(-2px);
  box-shadow: var(--card-shadow);
}
.article-card.low-score { opacity: 0.6; }
.card-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.card-meta { font-size: 12px; color: var(--text-secondary); }
.card-score { font-size: 12px; font-weight: 600; }
.score-high { color: #bc8cff; }
.score-mid { color: var(--accent); }
.score-low { color: var(--text-muted); }
.card-title { font-size: 15px; color: var(--text-primary); margin-bottom: 6px; line-height: 1.4; }
.card-summary { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.card-footer {
  display: flex; justify-content: space-between; margin-top: 12px;
  font-size: 11px; color: var(--text-muted);
}
.loading, .empty { text-align: center; padding: 60px 0; color: var(--text-secondary); }
.empty-hint { font-size: 13px; color: var(--text-muted); margin-top: 8px; }
</style>
```

- [ ] **步骤 3：创建 ArticleDetailView.vue**

`frontend/src/views/blog/ArticleDetailView.vue` — 1:2 分栏详情页：
```vue
<template>
  <div class="article-detail">
    <div class="detail-header">
      <button class="back-btn" @click="router.push('/blog')">← 返回</button>
      <div class="header-actions">
        <button class="action-btn" @click="handleExport" title="导出 MD">📥 导出</button>
        <button class="action-btn" @click="handleReprocess" title="重新处理">🔄 重新处理</button>
      </div>
    </div>

    <div v-if="!article" class="loading">加载中...</div>
    <div v-else class="detail-body">
      <!-- 左 1/3: AI 笔记 -->
      <div class="note-panel">
        <h1 class="article-title">{{ article.title }}</h1>
        <div class="article-meta">
          <span>Source: <a :href="article.url" target="_blank">{{ article.source_name }}</a></span>
          <span v-if="article.score" class="score-badge" :class="scoreClass">⭐ {{ article.score }}/10</span>
        </div>

        <div class="note-section">
          <h3 class="section-label summary-label">📋 Summary</h3>
          <div class="section-content">{{ article.summary || '暂无总结' }}</div>
        </div>

        <div class="note-section">
          <h3 class="section-label points-label">🔑 Key Points</h3>
          <div class="section-content">
            <template v-if="parsedKeyPoints.length">
              <ul class="points-list">
                <li v-for="(point, i) in parsedKeyPoints" :key="i">{{ point }}</li>
              </ul>
            </template>
            <template v-else>{{ article.key_points || '暂无要点' }}</template>
          </div>
        </div>

        <div v-if="article.deep_analysis" class="note-section">
          <h3 class="section-label analysis-label">🔬 Deep Analysis</h3>
          <div class="section-content">{{ article.deep_analysis }}</div>
        </div>
      </div>

      <!-- 右 2/3: 原文 -->
      <div class="source-panel">
        <div v-if="article.status === 'unparsable'" class="unparsable-notice">
          <p>⚠️ 无法提取正文内容</p>
          <a :href="article.url" target="_blank" class="open-link">在新标签页打开原文 →</a>
        </div>
        <template v-else>
          <iframe
            v-if="iframeOk"
            :src="article.url"
            class="source-iframe"
            @error="iframeOk = false"
          />
          <div v-else class="cached-content">
            <div class="cached-notice">⚠️ iframe 加载失败，展示缓存内容</div>
            <pre class="cached-text">{{ article.raw_text }}</pre>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useBlogStore } from "@/stores/blog";

const route = useRoute();
const router = useRouter();
const blogStore = useBlogStore();
const article = computed(() => blogStore.currentArticle);
const iframeOk = ref(true);

const scoreClass = computed(() => {
  if (!article.value?.score) return "";
  if (article.value.score >= 7) return "score-high";
  if (article.value.score >= 4) return "score-mid";
  return "score-low";
});

const parsedKeyPoints = computed(() => {
  const kp = article.value?.key_points;
  if (!kp) return [];
  try {
    const parsed = JSON.parse(kp);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
});

onMounted(() => {
  const id = Number(route.params.id);
  blogStore.fetchArticle(id);
  iframeOk.value = true;
});

async function handleExport() {
  if (!article.value) return;
  try {
    const blob = await blogStore.exportArticle(article.value.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${article.value.title.slice(0, 50)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  } catch { /* ignore */ }
}

async function handleReprocess() {
  if (!article.value) return;
  await blogStore.reprocessArticle(article.value.id);
  blogStore.fetchArticle(article.value.id);
}
</script>

<style scoped>
.article-detail { display: flex; flex-direction: column; height: calc(100vh - 52px - 48px); margin: -24px; }
.detail-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary); flex-shrink: 0;
}
.back-btn {
  background: none; border: none; color: var(--accent);
  cursor: pointer; font-size: 14px;
}
.header-actions { display: flex; gap: 8px; }
.action-btn {
  padding: 6px 12px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 12px;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
.detail-body { display: flex; flex: 1; overflow: hidden; }
.note-panel {
  width: 33.33%; border-right: 1px solid var(--border-primary);
  padding: 24px; overflow-y: auto;
}
.article-title { font-size: 20px; color: var(--text-primary); margin-bottom: 12px; line-height: 1.4; }
.article-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; font-size: 13px; color: var(--text-secondary); }
.article-meta a { color: var(--accent); }
.score-badge { font-weight: 600; }
.score-high { color: #bc8cff; }
.score-mid { color: var(--accent); }
.score-low { color: var(--text-muted); }
.note-section { margin-bottom: 20px; }
.section-label { font-size: 13px; margin-bottom: 8px; }
.summary-label { color: var(--accent); }
.points-label { color: #f78166; }
.analysis-label { color: #bc8cff; }
.section-content { font-size: 14px; color: var(--text-primary); line-height: 1.7; }
.points-list { padding-left: 18px; }
.points-list li { margin-bottom: 6px; }
.source-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-primary); }
.source-iframe { width: 100%; height: 100%; border: none; flex: 1; }
.cached-content { padding: 20px; overflow-y: auto; flex: 1; }
.cached-notice { color: var(--warning); font-size: 13px; margin-bottom: 12px; }
.cached-text { white-space: pre-wrap; font-size: 14px; color: var(--text-primary); line-height: 1.7; font-family: inherit; }
.unparsable-notice { padding: 60px 20px; text-align: center; color: var(--text-secondary); }
.unparsable-notice p { margin-bottom: 12px; }
.open-link { color: var(--accent); font-size: 14px; }
.loading { padding: 60px; text-align: center; color: var(--text-secondary); }
</style>
```

- [ ] **步骤 4：创建 BlogSettingsView.vue**

`frontend/src/views/blog/settings/BlogSettingsView.vue` — 4 Tab 设置页：
```vue
<template>
  <div class="blog-settings">
    <h1>知识笔记设置</h1>
    <div class="tabs">
      <button
        v-for="tab in tabs" :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- Tab 1: RSS 源管理 -->
    <div v-if="activeTab === 'rss'" class="tab-content">
      <div class="section-header">
        <h2>RSS 源 ({{ blogStore.rssSources.length }}/{{ rssLimit }})</h2>
        <button
          class="add-btn"
          :disabled="blogStore.rssSources.length >= rssLimit"
          @click="showAddRss = true"
        >+ 添加源</button>
      </div>
      <p v-if="blogStore.rssSources.length >= rssLimit" class="limit-warn">
        已达上限 {{ rssLimit }} 个
      </p>
      <table class="data-table">
        <thead><tr><th>名称</th><th>URL</th><th>间隔</th><th>上次抓取</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="src in blogStore.rssSources" :key="src.id">
            <td>{{ src.name }}</td>
            <td class="url-cell">{{ src.url }}</td>
            <td>{{ src.fetch_interval / 60 }}分钟</td>
            <td>{{ src.last_fetched ? formatDate(src.last_fetched) : '—' }}</td>
            <td>
              <button class="del-btn" @click="blogStore.deleteRSSSource(src.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="showAddRss" class="inline-form">
        <input v-model="newRss.name" placeholder="源名称" class="form-input" />
        <input v-model="newRss.url" placeholder="RSS URL" class="form-input" />
        <select v-model="newRss.category" class="form-select">
          <option :value="null">无分类</option>
          <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">
            {{ cat.icon }} {{ cat.name }}
          </option>
        </select>
        <button class="btn-primary" @click="addRss">添加</button>
        <button class="btn-cancel" @click="showAddRss = false">取消</button>
      </div>
    </div>

    <!-- Tab 2: 分类配置 -->
    <div v-if="activeTab === 'categories'" class="tab-content">
      <div class="section-header">
        <h2>分类管理</h2>
        <button class="add-btn" @click="showAddCat = true">+ 新建分类</button>
      </div>
      <div v-for="cat in blogStore.categories" :key="cat.id" class="cat-item">
        <div class="cat-header">
          <span>{{ cat.icon }} {{ cat.name }}</span>
          <span class="cat-count">{{ cat.article_count }} 篇</span>
          <button class="del-btn" @click="blogStore.deleteCategory(cat.id)">删除</button>
        </div>
        <div class="thresholds">
          <label>低分: <input type="number" :value="cat.score_thresholds?.low?.[1]" class="threshold-input" disabled /></label>
          <label>中分: <input type="number" :value="cat.score_thresholds?.mid?.[1]" class="threshold-input" disabled /></label>
          <label>高分: <input type="number" :value="cat.score_thresholds?.high?.[1]" class="threshold-input" disabled /></label>
        </div>
      </div>
      <div v-if="showAddCat" class="inline-form">
        <input v-model="newCat.name" placeholder="分类名" class="form-input" />
        <input v-model="newCat.icon" placeholder="图标 emoji" class="form-input" />
        <button class="btn-primary" @click="addCat">创建</button>
        <button class="btn-cancel" @click="showAddCat = false">取消</button>
      </div>
    </div>

    <!-- Tab 3: 评分设置 -->
    <div v-if="activeTab === 'scoring'" class="tab-content">
      <h2>评分与模型</h2>
      <div class="setting-row">
        <span>L1 模型（过滤）</span>
        <span class="setting-value">{{ blogStore.config?.l1_model || 'deepseek-chat' }}</span>
      </div>
      <div class="setting-row">
        <span>L2 模型（深度）</span>
        <span class="setting-value">{{ blogStore.config?.l2_model || 'glm-4-plus' }}</span>
      </div>
      <p class="hint">模型配置后续可在 AI 设置中修改</p>
    </div>

    <!-- Tab 4: 调度与工具 -->
    <div v-if="activeTab === 'tools'" class="tab-content">
      <h2>调度与工具</h2>
      <div class="tool-actions">
        <button class="action-btn" @click="handleFetchAll">🔄 全量抓取</button>
      </div>
      <h3 style="margin-top:24px">无效链接</h3>
      <table class="data-table">
        <thead><tr><th>URL</th><th>原因</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="f in blogStore.failedUrls" :key="f.id">
            <td class="url-cell">{{ f.url }}</td>
            <td>{{ f.reason }}</td>
            <td><button class="del-btn" @click="blogStore.deleteFailedUrl(f.id)">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useBlogStore } from "@/stores/blog";

const blogStore = useBlogStore();
const activeTab = ref("rss");
const showAddRss = ref(false);
const showAddCat = ref(false);
const newRss = ref({ name: "", url: "", category: null as number | null });
const newCat = ref({ name: "", icon: "📁" });

const rssLimit = computed(() => blogStore.config?.rss_source_limit || 40);

const tabs = [
  { key: "rss", label: "RSS 源" },
  { key: "categories", label: "分类" },
  { key: "scoring", label: "评分" },
  { key: "tools", label: "工具" },
];

onMounted(async () => {
  await Promise.all([
    blogStore.fetchRSSSources(),
    blogStore.fetchCategories(),
    blogStore.fetchConfig(),
    blogStore.fetchFailedUrls(),
  ]);
});

async function addRss() {
  if (!newRss.value.name || !newRss.value.url) return;
  await blogStore.createRSSSource({
    name: newRss.value.name,
    url: newRss.value.url,
    category: newRss.value.category,
  });
  newRss.value = { name: "", url: "", category: null };
  showAddRss.value = false;
}

async function addCat() {
  if (!newCat.value.name) return;
  await blogStore.createCategory({
    name: newCat.value.name,
    icon: newCat.value.icon,
    score_thresholds: { low: [1, 3], mid: [4, 6], high: [7, 10] },
  });
  newCat.value = { name: "", icon: "📁" };
  showAddCat.value = false;
}

async function handleFetchAll() {
  await blogStore.fetchAll();
  blogStore.fetchArticles();
}

function formatDate(dateStr: string) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString("zh-CN");
}
</script>

<style scoped>
.blog-settings { max-width: 900px; }
.blog-settings h1 { font-size: 24px; color: var(--text-primary); margin-bottom: 20px; }
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border-primary); margin-bottom: 20px; }
.tab {
  padding: 10px 20px; background: none; border: none; border-bottom: 2px solid transparent;
  color: var(--text-secondary); cursor: pointer; font-size: 14px;
}
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h2 { font-size: 16px; color: var(--text-primary); }
.add-btn {
  padding: 6px 14px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.add-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.limit-warn { color: var(--warning); font-size: 13px; margin-bottom: 12px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--border-primary); color: var(--text-secondary); }
.data-table td { padding: 8px; border-bottom: 1px solid var(--border-secondary); color: var(--text-primary); }
.url-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn { background: none; border: 1px solid var(--border-primary); border-radius: var(--radius-sm); color: var(--error); cursor: pointer; padding: 4px 8px; font-size: 12px; }
.inline-form { display: flex; gap: 8px; margin-top: 16px; align-items: center; flex-wrap: wrap; }
.form-input, .form-select {
  padding: 8px 10px; background: var(--input-bg); border: 1px solid var(--input-border);
  border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px;
}
.btn-primary {
  padding: 8px 14px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.btn-cancel {
  padding: 8px 14px; background: none; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 13px;
}
.cat-item {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 12px 16px; margin-bottom: 8px;
}
.cat-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.cat-count { font-size: 12px; color: var(--text-muted); }
.thresholds { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.threshold-input {
  width: 40px; padding: 4px; text-align: center; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 12px;
}
.setting-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border-secondary); }
.setting-value { color: var(--text-primary); }
.hint { font-size: 12px; color: var(--text-muted); margin-top: 12px; }
.tool-actions { margin-bottom: 16px; }
.action-btn {
  padding: 8px 16px; background: var(--card-bg); border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-primary); cursor: pointer; font-size: 13px;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
</style>
```

- [ ] **步骤 5：更新路由**

修改 `frontend/src/router/index.ts`，在 children 数组中追加：
```typescript
{
  path: "blog",
  children: [
    { path: "", name: "blog", component: () => import("@/views/blog/BlogListView.vue") },
    { path: "settings", name: "blog-settings", component: () => import("@/views/blog/settings/BlogSettingsView.vue") },
    { path: ":id", name: "blog-article", component: () => import("@/views/blog/ArticleDetailView.vue") },
  ],
},
```

- [ ] **步骤 6：验证前端构建**

运行：`cd E:\WSL\musk\frontend && npx vue-tsc --noEmit`
预期：无类型错误

- [ ] **步骤 7：Commit**

```bash
cd E:\WSL\musk
git add frontend/src/
git commit -m "feat(blog): 实现前端列表页 + 详情页 + 设置页"
```

---

## 任务 9：端到端验证

- [ ] **步骤 1：运行后端全量测试**

运行：`cd E:\WSL\musk\backend && python -m pytest tests/ -v`
预期：所有测试 PASS

- [ ] **步骤 2：启动开发服务器验证**

运行：`cd E:\WSL\musk\backend && python manage.py runserver`
验证：
1. 访问 `/api/modules/` 返回 blog 模块信息
2. 访问 `/api/blog/categories/` 返回空列表
3. 访问 `/api/blog/articles/` 返回空列表

- [ ] **步骤 3：启动前端验证**

运行：`cd E:\WSL\musk\frontend && npm run build`
预期：构建成功无错误

- [ ] **步骤 4：最终 Commit**

```bash
cd E:\WSL\musk
git add -A
git commit -m "feat(blog): 博客引擎模块完成"
```
