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
    summary = models.TextField(blank=True, default="")
    key_points = models.TextField(blank=True, default="")
    deep_analysis = models.TextField(blank=True, default="")
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
