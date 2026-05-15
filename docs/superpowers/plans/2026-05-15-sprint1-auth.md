# Sprint 1: 项目脚手架 + 认证系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 搭建 Vue 3 + Django 4 项目骨架，实现完整的 JWT 认证闭环（注册 → 登录 → 首页 → Token 刷新）。

**架构：** 前后端分离。Django 后端提供 REST API（DRF + SimpleJWT），Vue 3 前端通过 Axios 调用 API，JWT 存储在 localStorage，Axios 拦截器自动附带 Token。暗夜科技深色主题（Sprint 2 前仅基础样式）。

**技术栈：** Vue 3 + TypeScript + Vite + Pinia + Vue Router + Axios | Django 4.2 + DRF + SimpleJWT + SQLite | pytest + pytest-django

---

## 文件结构

```
musk/                                  # 项目根目录 (E:\WSL\musk)
├── .gitignore
├── .env.example
├── CLAUDE.md                          # 已存在
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── musk/
│   │   ├── __init__.py
│   │   ├── settings.py                # Django 配置：DB/JWT/CORS/INSTALLED_APPS
│   │   ├── urls.py                    # 根路由：include auth URLs
│   │   └── wsgi.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── models.py              # 自定义 User 模型（默认 is_staff=True）
│   │       ├── serializers.py         # 注册/用户序列化器
│   │       ├── views.py               # RegisterView, MeView
│   │       └── urls.py                # /api/auth/* 路由
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # pytest fixtures
│       └── test_auth.py               # 认证 API 测试
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts                 # 开发代理 /api → localhost:8000
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── index.html
│   ├── env.d.ts
│   └── src/
│       ├── main.ts                    # Vue 入口
│       ├── App.vue                    # 根组件（router-view）
│       ├── router/
│       │   └── index.ts               # 路由：/login, /, 路由守卫
│       ├── stores/
│       │   └── auth.ts                # Pinia auth store
│       ├── core/
│       │   └── api.ts                 # Axios 实例 + JWT 拦截器
│       ├── views/
│       │   ├── LoginView.vue          # 登录/注册表单
│       │   └── HomeView.vue           # 空白首页
│       └── styles/
│           └── variables.css          # CSS Variables（暗夜科技主题基础）
│
├── data/                              # SQLite 文件（gitignore）
└── docs/                              # 已存在
```

---

## 任务 1：项目脚手架与 Git 初始化

**文件：**
- 创建：`.gitignore`
- 创建：`.env.example`

- [ ] **步骤 1：初始化 Git 仓库**

```bash
cd /e/WSL/musk
git init
```

- [ ] **步骤 2：创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/
env/

# Django
*.db
data/
media/

# Node
node_modules/
frontend/dist/

# Environment
.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Superpowers (local)
.superpowers/
```

- [ ] **步骤 3：创建 .env.example**

```env
# Django
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_DIR=data

# JWT
JWT_ACCESS_TTL_MINUTES=30
JWT_REFRESH_TTL_DAYS=7

# AI (Sprint 3+)
DEEPSEEK_API_KEY=
GLM_API_KEY=
```

- [ ] **步骤 4：创建数据目录**

```bash
mkdir -p data
```

- [ ] **步骤 5：Commit 项目脚手架**

```bash
git add .gitignore .env.example
git commit -m "chore: 初始化项目脚手架与配置文件"
```

---

## 任务 2：Django 后端项目初始化

**文件：**
- 创建：`backend/requirements.txt`
- 创建：`backend/manage.py`
- 创建：`backend/musk/__init__.py`
- 创建：`backend/musk/settings.py`
- 创建：`backend/musk/urls.py`
- 创建：`backend/musk/wsgi.py`
- 创建：`backend/core/__init__.py`
- 创建：`backend/core/auth/__init__.py`

- [ ] **步骤 1：创建后端目录结构**

```bash
mkdir -p backend/musk backend/core/auth backend/tests
```

- [ ] **步骤 2：创建 requirements.txt**

```txt
Django==4.2.*
djangorestframework==3.15.*
djangorestframework-simplejwt==5.3.*
django-cors-headers==4.3.*
python-dotenv==1.0.*
pytest==8.2.*
pytest-django==4.8.*
```

- [ ] **步骤 3：创建 Python 虚拟环境并安装依赖**

```bash
cd /e/WSL/musk/backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

- [ ] **步骤 4：创建 manage.py**

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musk.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

- [ ] **步骤 5：创建 musk/settings.py**

```python
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-me")

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local
    "core.auth",
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

# Database — SQLite at data/musk.db
DB_DIR = os.getenv("DB_DIR", "data")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(BASE_DIR).parent / DB_DIR / "musk.db",
    }
}

AUTH_USER_MODEL = "auth.User"

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TTL_MINUTES", "30"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TTL_DAYS", "7"))
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS — 开发环境允许前端访问
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

- [ ] **步骤 6：创建 musk/urls.py**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("core.auth.urls")),
]
```

- [ ] **步骤 7：创建 musk/__init__.py（空文件）**

```python
```

- [ ] **步骤 8：创建 musk/wsgi.py**

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musk.settings")

application = get_wsgi_application()
```

- [ ] **步骤 9：创建 core/__init__.py 和 core/auth/__init__.py（空文件）**

```python
```

- [ ] **步骤 10：验证 Django 项目可启动**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python manage.py check
```

预期输出：`System check identified no issues (0 silenced).`

- [ ] **步骤 11：Commit 后端骨架**

```bash
cd /e/WSL/musk
git add backend/
git commit -m "chore: 初始化 Django 后端项目骨架"
```

---

## 任务 3：自定义 User 模型

**文件：**
- 创建：`backend/core/auth/models.py`

- [ ] **步骤 1：编写 User 模型测试**

创建 `backend/tests/__init__.py`（空文件）和 `backend/tests/conftest.py`：

```python
import sys
from pathlib import Path

# 确保后端目录在 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
```

创建 `backend/tests/test_auth.py`：

```python
import pytest
from django.test import TestCase
from core.auth.models import User


@pytest.mark.django_db
class TestUserModel(TestCase):
    def test_create_user_defaults_to_staff(self):
        """注册用户默认拥有 staff 和 superuser 权限"""
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_create_user_with_email(self):
        """可选填 email"""
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        assert user.email == "test@example.com"
```

- [ ] **步骤 2：创建 pytest 配置文件**

创建 `backend/pytest.ini`：

```ini
[pytest]
DJANGO_SETTINGS_MODULE = musk.settings
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **步骤 3：运行测试，确认失败**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python -m pytest tests/test_auth.py -v
```

预期：FAIL（`ModuleNotFoundError: No module named 'core.auth.models'`）

- [ ] **步骤 4：实现 User 模型**

创建 `backend/core/auth/models.py`：

```python
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Musk 平台用户模型 — 所有用户默认拥有 admin 权限。"""

    class Meta:
        db_table = "auth_user"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def save(self, *args, **kwargs):
        # 新用户默认赋予 staff + superuser 权限
        if self._state.adding:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)
```

更新 `backend/core/auth/__init__.py`（注册 default_app_config 无需在 Django 4.2+ 手动设置，但需要确保 APP 配置正确）。创建 `backend/core/auth/apps.py`：

```python
from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.auth"
    label = "core_auth"
    verbose_name = "认证服务"
```

更新 `backend/core/auth/__init__.py`：

```python
default_app_config = "core.auth.apps.AuthConfig"
```

更新 `backend/musk/settings.py` 中 `AUTH_USER_MODEL`：

```python
AUTH_USER_MODEL = "core_auth.User"
```

更新 `backend/musk/settings.py` 中 `INSTALLED_APPS`，将 `"core.auth"` 改为：

```python
    "core.auth.apps.AuthConfig",
```

- [ ] **步骤 5：执行数据库迁移**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python manage.py makemigrations core_auth
python manage.py migrate
```

预期：无错误，`data/musk.db` 创建成功。

- [ ] **步骤 6：运行测试，确认通过**

```bash
python -m pytest tests/test_auth.py -v
```

预期：2 passed

- [ ] **步骤 7：Commit User 模型**

```bash
cd /e/WSL/musk
git add backend/core/auth/ backend/tests/ backend/pytest.ini
git commit -m "feat(auth): 实现自定义 User 模型，默认 admin 权限"
```

---

## 任务 4：注册 API

**文件：**
- 修改：`backend/tests/test_auth.py`（追加测试）
- 创建：`backend/core/auth/serializers.py`
- 创建：`backend/core/auth/views.py`
- 修改：`backend/core/auth/urls.py`

- [ ] **步骤 1：编写注册 API 测试**

在 `backend/tests/test_auth.py` 末尾追加：

```python
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestRegisterAPI(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        """正常注册返回 access 和 refresh token"""
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "newuser", "password": "strongpass123"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["username"] == "newuser"

    def test_register_missing_password(self):
        """缺少密码返回 400"""
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "newuser"},
            format="json",
        )
        assert resp.status_code == 400

    def test_register_duplicate_username(self):
        """重复用户名返回 400"""
        self.client.post(
            "/api/auth/register/",
            {"username": "dup", "password": "pass123"},
            format="json",
        )
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "dup", "password": "pass456"},
            format="json",
        )
        assert resp.status_code == 400
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python -m pytest tests/test_auth.py::TestRegisterAPI -v
```

预期：FAIL（404 或 URL 不存在）

- [ ] **步骤 3：创建序列化器**

创建 `backend/core/auth/serializers.py`：

```python
from rest_framework import serializers
from core.auth.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"email": {"required": False}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff", "is_superuser")
        read_only_fields = ("id", "is_staff", "is_superuser")
```

- [ ] **步骤 4：创建注册视图**

创建 `backend/core/auth/views.py`：

```python
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.auth.models import User
from core.auth.serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """用户注册 — 注册成功自动返回 JWT。"""

    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    """获取当前登录用户信息。"""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
```

- [ ] **步骤 5：创建 URL 路由**

创建 `backend/core/auth/urls.py`：

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.auth.views import RegisterView, MeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
```

- [ ] **步骤 6：运行注册 API 测试**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python -m pytest tests/test_auth.py::TestRegisterAPI -v
```

预期：3 passed

- [ ] **步骤 7：Commit 注册 API**

```bash
cd /e/WSL/musk
git add backend/core/auth/ backend/tests/
git commit -m "feat(auth): 实现用户注册 API（返回 JWT）"
```

---

## 任务 5：登录 + Token 刷新 + 当前用户 API

**文件：**
- 修改：`backend/tests/test_auth.py`（追加测试）

- [ ] **步骤 1：编写登录/刷新/用户信息测试**

在 `backend/tests/test_auth.py` 末尾追加：

```python
@pytest.mark.django_db
class TestLoginAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        # 先注册一个用户
        self.client.post(
            "/api/auth/register/",
            {"username": "loginuser", "password": "testpass123"},
            format="json",
        )

    def test_login_success(self):
        """登录返回 access 和 refresh"""
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_wrong_password(self):
        """密码错误返回 401"""
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": "wrongpass"},
            format="json",
        )
        assert resp.status_code == 401

    def test_token_refresh(self):
        """refresh token 可获取新 access token"""
        login_resp = self.client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": "testpass123"},
            format="json",
        )
        refresh_token = login_resp.json()["refresh"]

        resp = self.client.post(
            "/api/auth/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.json()


@pytest.mark.django_db
class TestMeAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        reg = self.client.post(
            "/api/auth/register/",
            {"username": "meuser", "password": "testpass123"},
            format="json",
        )
        self.access_token = reg.json()["access"]

    def test_me_authenticated(self):
        """已认证用户可获取自身信息"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        resp = self.client.get("/api/auth/me/", format="json")
        assert resp.status_code == 200
        assert resp.json()["username"] == "meuser"

    def test_me_unauthenticated(self):
        """未认证返回 401"""
        resp = self.client.get("/api/auth/me/", format="json")
        assert resp.status_code == 401
```

- [ ] **步骤 2：运行全部测试**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python -m pytest tests/test_auth.py -v
```

预期：全部通过（RegisterView + TokenObtainPairView + TokenRefreshView + MeView，共约 8 个测试）

- [ ] **步骤 3：Commit 认证 API 测试**

```bash
cd /e/WSL/musk
git add backend/tests/
git commit -m "test(auth): 完整认证 API 测试（注册/登录/刷新/用户信息）"
```

---

## 任务 6：Vue 3 前端项目初始化

**文件：**
- 创建：`frontend/` 整个目录（由 create-vue 脚手架生成）
- 修改：`frontend/vite.config.ts`（添加 API 代理）
- 创建：`frontend/src/styles/variables.css`

- [ ] **步骤 1：用 create-vue 创建前端项目**

```bash
cd /e/WSL/musk
npm create vue@latest frontend -- --typescript --router --pinia
```

交互选项选择：
- TypeScript: Yes
- JSX: No
- Router: Yes
- Pinia: Yes
- Vitest: No（Sprint 1 先跳过前端测试）
- E2E: No
- ESLint: No（Sprint 1 先跳过，后续补充）

- [ ] **步骤 2：安装额外依赖**

```bash
cd /e/WSL/musk/frontend
npm install axios
```

- [ ] **步骤 3：配置 Vite 开发代理**

修改 `frontend/vite.config.ts`：

```typescript
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **步骤 4：创建 CSS Variables 基础主题**

创建 `frontend/src/styles/variables.css`：

```css
:root {
  /* 暗夜科技深色主题（默认） */
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-sidebar: #010409;
  --bg-card: #161b22;
  --border: #21262d;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --accent: #58a6ff;
  --accent-hover: #79b8ff;
  --accent-secondary: #7c3aed;
  --danger: #f85149;
  --success: #3fb950;
  --warning: #d29922;

  --radius: 6px;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
}

[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f6f8fa;
  --bg-sidebar: #f0f0f5;
  --bg-card: #ffffff;
  --border: #d0d7de;
  --text-primary: #24292f;
  --text-secondary: #57606a;
  --accent: #0969da;
  --accent-hover: #0550ae;
  --accent-secondary: #6f42c1;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

- [ ] **步骤 5：验证前端可启动**

```bash
cd /e/WSL/musk/frontend
npm run dev
```

预期：Vite 输出 `Local: http://localhost:5173/`，浏览器打开可见 Vue 默认页面。确认后停止。

- [ ] **步骤 6：Commit 前端骨架**

```bash
cd /e/WSL/musk
git add frontend/
git commit -m "chore: 初始化 Vue 3 + TypeScript 前端项目"
```

---

## 任务 7：前端 API 层与认证 Store

**文件：**
- 创建：`frontend/src/core/api.ts`
- 创建：`frontend/src/stores/auth.ts`
- 修改：`frontend/src/main.ts`（导入 CSS 变量）

- [ ] **步骤 1：创建 Axios 实例 + JWT 拦截器**

创建 `frontend/src/core/api.ts`：

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器：自动附带 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：access token 过期时尝试刷新
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 仅对 401 且未重试过的请求刷新
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      localStorage.getItem("refresh")
    ) {
      originalRequest._retry = true;

      try {
        const { data } = await axios.post("/api/auth/refresh/", {
          refresh: localStorage.getItem("refresh"),
        });
        localStorage.setItem("access", data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch {
        // 刷新也失败 → 清除 token，跳转登录
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **步骤 2：创建 Pinia Auth Store**

创建 `frontend/src/stores/auth.ts`：

```typescript
import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

interface User {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_superuser: boolean;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const isAuthenticated = ref(!!localStorage.getItem("access"));

  async function register(username: string, password: string, email?: string) {
    const payload: Record<string, string> = { username, password };
    if (email) payload.email = email;

    const { data } = await api.post("/auth/register/", payload);
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    user.value = data.user;
    isAuthenticated.value = true;
    return data;
  }

  async function login(username: string, password: string) {
    const { data } = await api.post("/auth/login/", { username, password });
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    // TokenObtainPairView 不返回 user，需要单独获取
    await fetchUser();
    return data;
  }

  async function fetchUser() {
    try {
      const { data } = await api.get("/auth/me/");
      user.value = data;
      isAuthenticated.value = true;
    } catch {
      logout();
    }
  }

  function logout() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    user.value = null;
    isAuthenticated.value = false;
  }

  return { user, isAuthenticated, register, login, fetchUser, logout };
});
```

- [ ] **步骤 3：更新 main.ts**

修改 `frontend/src/main.ts`：

```typescript
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/variables.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
```

- [ ] **步骤 4：Commit API 层和 Store**

```bash
cd /e/WSL/musk
git add frontend/src/core/ frontend/src/stores/ frontend/src/main.ts
git commit -m "feat(frontend): 实现 API 层（JWT 拦截器）与认证 Store"
```

---

## 任务 8：路由守卫与页面组件

**文件：**
- 修改：`frontend/src/router/index.ts`
- 创建：`frontend/src/views/LoginView.vue`
- 创建：`frontend/src/views/HomeView.vue`
- 修改：`frontend/src/App.vue`

- [ ] **步骤 1：配置路由与守卫**

修改 `frontend/src/router/index.ts`：

```typescript
import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { requiresAuth: false },
    },
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to) => {
  const isAuthenticated = !!localStorage.getItem("access");

  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: "login" };
  }

  if (to.name === "login" && isAuthenticated) {
    return { name: "home" };
  }
});

export default router;
```

- [ ] **步骤 2：创建登录/注册页面**

创建 `frontend/src/views/LoginView.vue`：

```vue
<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>Musk</h1>
        <p>看板工具平台</p>
      </div>

      <div class="tab-bar">
        <button
          :class="['tab', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button
          :class="['tab', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >
          注册
        </button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
          />
        </div>

        <div v-if="mode === 'register'" class="form-group">
          <label for="email">邮箱（可选）</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入邮箱"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码（至少 8 位）"
            required
            minlength="8"
            autocomplete="current-password"
          />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? "处理中..." : mode === "login" ? "登录" : "注册" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const mode = ref<"login" | "register">("login");
const username = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function handleSubmit() {
  error.value = "";
  loading.value = true;

  try {
    if (mode.value === "register") {
      await authStore.register(username.value, password.value, email.value || undefined);
    } else {
      await authStore.login(username.value, password.value);
    }
    router.push({ name: "home" });
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string; username?: string[] } } };
    if (err.response?.data) {
      const data = err.response.data;
      error.value = data.detail || data.username?.[0] || "操作失败，请检查输入";
    } else {
      error.value = "网络错误，请稍后重试";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

.login-card {
  width: 400px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-header h1 {
  font-size: 28px;
  color: var(--accent);
  margin-bottom: 4px;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.tab {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: var(--accent);
}

.error {
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 12px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
```

- [ ] **步骤 3：创建空白首页**

创建 `frontend/src/views/HomeView.vue`：

```vue
<template>
  <div class="home">
    <div class="home-header">
      <h1>欢迎回来，{{ authStore.user?.username || "用户" }}</h1>
      <button class="logout-btn" @click="handleLogout">退出登录</button>
    </div>
    <p class="home-subtitle">Musk 看板工具平台 — Sprint 1 骨架验证</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser();
  }
});

function handleLogout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.home {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.home-header h1 {
  font-size: 24px;
  color: var(--text-primary);
}

.home-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.logout-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.logout-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
}
</style>
```

- [ ] **步骤 4：更新 App.vue**

修改 `frontend/src/App.vue`：

```vue
<template>
  <router-view />
</template>
```

- [ ] **步骤 5：删除脚手架默认生成的无用文件**

```bash
cd /e/WSL/musk/frontend/src
rm -rf components/HelloWorld.vue components/TheWelcome.vue components/WelcomeItem.vue components/icons/
rm -rf assets/base.css assets/logo.svg assets/main.css
rm -rf views/HomeView.vue.bak 2>/dev/null
```

如果 `views/` 目录下有 `AboutView.vue`，也删除：

```bash
rm -f views/AboutView.vue
```

如果 `stores/` 目录下有 `counter.ts` 或类似默认 store，也删除：

```bash
rm -f stores/counter.ts
```

- [ ] **步骤 6：Commit 页面组件**

```bash
cd /e/WSL/musk
git add frontend/src/
git commit -m "feat(frontend): 实现登录/注册页面与路由守卫"
```

---

## 任务 9：端到端集成验证

- [ ] **步骤 1：启动 Django 后端**

终端 1：

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python manage.py runserver
```

预期：`Starting development server at http://127.0.0.1:8000/`

- [ ] **步骤 2：启动 Vue 前端**

终端 2：

```bash
cd /e/WSL/musk/frontend
npm run dev
```

预期：`Local: http://localhost:5173/`

- [ ] **步骤 3：验证注册流程**

浏览器打开 `http://localhost:5173`：
1. 自动跳转到 `/login`（因未认证）
2. 切换到「注册」标签
3. 输入用户名 `testuser`，密码 `testpass123`
4. 点击「注册」
5. 成功后跳转到首页，显示「欢迎回来，testuser」
6. 首页可点击「退出登录」回到登录页

- [ ] **步骤 4：验证登录流程**

1. 在登录标签输入 `testuser` / `testpass123`
2. 点击「登录」
3. 成功跳转到首页

- [ ] **步骤 5：验证 Token 刷新**

1. 登录后等待 30 秒或手动在浏览器 DevTools Console 执行：

```javascript
// 模拟 access 过期
localStorage.setItem("access", "expired-token");
```

2. 刷新页面，系统应自动用 refresh token 获取新 access token 并正常显示

- [ ] **步骤 6：运行后端测试套件**

```bash
cd /e/WSL/musk/backend
source .venv/Scripts/activate
python -m pytest tests/ -v
```

预期：全部通过

- [ ] **步骤 7：创建 .env 文件**

```bash
cp .env.example .env
# 编辑 .env 中的 SECRET_KEY 为一个真实随机字符串
```

- [ ] **步骤 8：最终 Commit**

```bash
cd /e/WSL/musk
git add -A
git commit -m "chore: Sprint 1 完成 — 项目脚手架 + JWT 认证闭环"
```

---

## 自检清单

| 检查项 | 结果 |
|--------|------|
| 规格覆盖：User 模型默认 admin | ✅ 任务 3 |
| 规格覆盖：注册 API | ✅ 任务 4 |
| 规格覆盖：登录 API | ✅ 任务 5（SimpleJWT TokenObtainPairView） |
| 规格覆盖：Token 刷新 | ✅ 任务 5（SimpleJWT TokenRefreshView） |
| 规格覆盖：获取当前用户 | ✅ 任务 5（MeView） |
| 规格覆盖：前端登录页 | ✅ 任务 8 |
| 规格覆盖：JWT 拦截器 | ✅ 任务 7 |
| 规格覆盖：路由守卫 | ✅ 任务 8 |
| 规格覆盖：.env 配置 | ✅ 任务 1 |
| 占位符扫描 | 无 TODO/TBD |
| 类型一致性 | api.ts 使用 auth store，store 使用 api.ts，视图使用 store — 一致 |
