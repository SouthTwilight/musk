import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-change-me-in-production"
)

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "core.auth.apps.AuthConfig",
    "core.config.apps.ConfigConfig",
    "core.storage.apps.StorageConfig",
    "core.ai.apps.AiConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "musk.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "musk.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "musk.wsgi.application"

# Database
db_dir = os.environ.get("DB_DIR", str(BASE_DIR.parent / "data"))
if not os.path.isabs(db_dir):
    db_dir = str(BASE_DIR.parent / db_dir)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(db_dir, "musk.db"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User model
AUTH_USER_MODEL = "core_auth.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TTL_MINUTES", 30))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.environ.get("JWT_REFRESH_TTL_DAYS", 7))
    ),
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "media"

# AI Configuration
AI_DEFAULT_MODEL = os.environ.get("AI_DEFAULT_MODEL", "deepseek")

# Logging — 日志落盘
LOG_DIR = os.environ.get("LOG_DIR", str(BASE_DIR.parent / "logs"))
if not os.path.isabs(LOG_DIR):
    LOG_DIR = str(BASE_DIR.parent / LOG_DIR)
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname:7s} {name} | {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname:7s} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # 主日志 — 所有模块
        "file_all": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "musk.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # 错误日志 — 仅 WARNING 及以上
        "file_error": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "musk-error.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # 博客模块专用日志
        "file_blog": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "blog.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        # AI 模块专用日志
        "file_ai": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "ai.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # Django 框架
        "django": {
            "handlers": ["console", "file_all"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file_error"],
            "level": "WARNING",
            "propagate": False,
        },
        # Musk 核心
        "core": {
            "handlers": ["console", "file_all"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core.ai": {
            "handlers": ["console", "file_ai"],
            "level": "DEBUG",
            "propagate": False,
        },
        # 模块应用层
        "module_layer": {
            "handlers": ["console", "file_all"],
            "level": "INFO",
            "propagate": False,
        },
        # 博客引擎
        "apps.blog": {
            "handlers": ["console", "file_blog"],
            "level": "DEBUG",
            "propagate": False,
        },
        # 请求日志
        "musk.request": {
            "handlers": ["console", "file_all"],
            "level": "INFO",
            "propagate": False,
        },
    },
    # root logger — 兜底
    "root": {
        "handlers": ["console", "file_all"],
        "level": "INFO",
    },
}

# Module Layer — 扫描并注册模块
import module_layer.scanner as _scanner
_SCANNED = False


def _ensure_modules_scanned():
    global _SCANNED
    if not _SCANNED:
        _SCANNED = True
        _scanner.scan_modules()


_ensure_modules_scanned()

# 动态添加已注册模块到 INSTALLED_APPS
for _info in _scanner.registry.all():
    _app_config = f"apps.{_info.name}.apps.{_info.name.capitalize()}Config"
    _app_path = f"apps.{_info.name}"
    if _app_config not in INSTALLED_APPS and _app_path not in INSTALLED_APPS:
        try:
            # Try to use the AppConfig class
            INSTALLED_APPS.append(_app_config)
        except Exception:
            INSTALLED_APPS.append(_app_path)

# 动态添加模块数据库
_MODULE_DBS = _scanner.get_module_databases()
for _alias, _config in _MODULE_DBS.items():
    DATABASES[_alias] = _config

# 数据库路由器
DATABASE_ROUTERS = ["module_layer.db_router.ModuleRouter"]

# 将扫描到的模块 URL 动态包含
# (在 urls.py 中处理)
