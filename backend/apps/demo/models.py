from django.db import models


class DemoItem(models.Model):
    """示例数据模型 — 验证独立数据库。"""
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "apps_demo"
        db_table = "demo_item"
        ordering = ["-created_at"]
