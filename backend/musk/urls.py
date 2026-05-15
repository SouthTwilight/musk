from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import module_layer.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("core.auth.urls")),
    path("api/config/", include("core.config.urls")),
    path("api/storage/", include("core.storage.urls")),
    path("api/ai/", include("core.ai.urls")),
    path("api/modules/", module_layer.views.ModuleListView.as_view(), name="module-list"),
]

# 动态注册模块 URL
from module_layer.registry import registry as _registry
import importlib
import logging

_logger = logging.getLogger(__name__)

for _info in _registry.all():
    try:
        _mod_urls = importlib.import_module(f"apps.{_info.name}.urls")
        urlpatterns.append(
            path(f"api/{_info.name}/", include(_mod_urls))
        )
    except (ImportError, Exception) as e:
        _logger.warning("Failed to load URLs for module %s: %s", _info.name, e)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
