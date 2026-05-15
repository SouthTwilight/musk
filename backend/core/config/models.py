from django.db import models
from django.conf import settings


class UserConfig(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="config",
    )
    theme = models.CharField(
        max_length=10,
        default="dark",
        choices=[("dark", "深色"), ("light", "浅色")],
    )
    background_image = models.CharField(max_length=500, blank=True, default="")
    sidebar_collapsed = models.BooleanField(default=False)

    class Meta:
        db_table = "user_config"
        verbose_name = "用户配置"
        verbose_name_plural = "用户配置"

    def __str__(self):
        return f"{self.user.username} 配置"
