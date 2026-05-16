import os
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
    label = "apps_blog"
    verbose_name = "知识笔记"

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true" or os.environ.get("START_SCHEDULER") == "1":
            try:
                from apps.blog.scheduler import start_scheduler
                start_scheduler()
            except Exception:
                pass
