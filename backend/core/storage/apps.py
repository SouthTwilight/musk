from django.apps import AppConfig


class StorageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.storage"
    label = "core_storage"
    verbose_name = "存储管理"
