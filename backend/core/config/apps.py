from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.config"
    label = "core_config"
    verbose_name = "配置管理"
