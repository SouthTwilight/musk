# Sprint 2: 框架壳 + 主题系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。

**目标：** 实现完整的应用布局壳（可折叠侧边栏 + 顶栏 + 内容区）、暗夜科技/浅色双主题切换、背景图上传系统。

**架构：** 前端布局壳作为 authenticated 路由的容器组件，侧边栏从顶到底，顶栏含 Logo/面包屑/主题切换/用户菜单。后端新增 UserConfig 模型持久化用户偏好（主题、背景图），Storage API 处理文件上传。

**技术栈：** Vue 3 + SCSS（布局壳）+ CSS Variables（主题）| Django + DRF（配置/文件上传）

**验证标准：** 登录后看到完整布局 → 侧边栏可折叠 → 主题可切换（持久化）→ 可上传背景图

---

## 文件结构

```
新增文件：
frontend/
├── src/
│   ├── shell/
│   │   ├── AppLayout.vue         # 认证后的布局容器
│   │   ├── Sidebar.vue           # 可折叠侧边栏
│   │   ├── TopBar.vue            # 顶部栏
│   │   └── UserMenu.vue          # 用户下拉菜单
│   ├── stores/
│   │   └── app.ts                # 应用状态 Store（侧边栏折叠、主题）
│   ├── composables/
│   │   └── useTheme.ts           # 主题切换逻辑
│   └── views/
│       └── SettingsView.vue      # 设置页面（背景图上传等）

backend/
├── core/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py             # UserConfig 模型
│   │   ├── serializers.py
│   │   ├── views.py              # 配置 CRUD + 文件上传
│   │   └── urls.py
│   └── storage/
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py             # UploadedFile 模型
│       ├── serializers.py
│       ├── views.py              # 文件上传/列表/删除
│       └── urls.py

修改文件：
frontend/src/router/index.ts      # 添加布局嵌套
frontend/src/views/HomeView.vue   # 简化为内容区展示
frontend/src/App.vue              # 保持 router-view
backend/musk/settings.py          # 添加 config/storage apps, MEDIA 配置
backend/musk/urls.py              # 添加 config/storage URLs
```

---

## 任务 1：后端 — UserConfig 模型 + API

### 1.1 创建 core/config Django App

**创建文件：**

- `backend/core/config/__init__.py`
- `backend/core/config/apps.py`：
```python
from django.apps import AppConfig

class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.config"
    label = "core_config"
    verbose_name = "配置管理"
```

- `backend/core/config/models.py`：
```python
from django.db import models
from django.conf import settings


class UserConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="config")
    theme = models.CharField(max_length=10, default="dark", choices=[("dark", "深色"), ("light", "浅色")])
    background_image = models.CharField(max_length=500, blank=True, default="")
    sidebar_collapsed = models.BooleanField(default=False)

    class Meta:
        db_table = "user_config"
        verbose_name = "用户配置"
        verbose_name_plural = "用户配置"

    def __str__(self):
        return f"{self.user.username} 配置"
```

- `backend/core/config/serializers.py`：
```python
from rest_framework import serializers
from core.config.models import UserConfig


class UserConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConfig
        fields = ("theme", "background_image", "sidebar_collapsed")
        read_only_fields = ()
```

- `backend/core/config/views.py`：
```python
from rest_framework import generics
from core.config.models import UserConfig
from core.config.serializers import UserConfigSerializer


class MyConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = UserConfigSerializer

    def get_object(self):
        config, _ = UserConfig.objects.get_or_create(user=self.request.user)
        return config
```

- `backend/core/config/urls.py`：
```python
from django.urls import path
from core.config.views import MyConfigView

urlpatterns = [
    path("", MyConfigView.as_view(), name="my-config"),
]
```

### 1.2 创建 core/storage Django App

- `backend/core/storage/__init__.py`
- `backend/core/storage/apps.py`：
```python
from django.apps import AppConfig

class StorageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.storage"
    label = "core_storage"
    verbose_name = "存储管理"
```

- `backend/core/storage/models.py`：
```python
from django.db import models
from django.conf import settings


class UploadedFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="uploads/%Y%m/")
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "uploaded_file"
        ordering = ["-created_at"]
```

- `backend/core/storage/serializers.py`：
```python
from rest_framework import serializers
from core.storage.models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ("id", "file", "filename", "created_at")
        read_only_fields = ("id", "created_at")
```

- `backend/core/storage/views.py`：
```python
from rest_framework import generics, parsers, status
from rest_framework.response import Response
from core.storage.models import UploadedFile
from core.storage.serializers import UploadedFileSerializer


class FileListView(generics.ListCreateAPIView):
    serializer_class = UploadedFileSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            filename=self.request.FILES["file"].name,
        )


class FileDetailView(generics.DestroyAPIView):
    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)
```

- `backend/core/storage/urls.py`：
```python
from django.urls import path
from core.storage.views import FileListView, FileDetailView

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("<int:pk>/", FileDetailView.as_view(), name="file-detail"),
]
```

### 1.3 更新 settings.py 和 urls.py

在 `INSTALLED_APPS` 中添加 `"core.config.apps.ConfigConfig"` 和 `"core.storage.apps.StorageConfig"`。

添加 MEDIA 配置：
```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "media"
```

更新 `musk/urls.py` 添加新路由：
```python
path("api/config/", include("core.config.urls")),
path("api/storage/", include("core.storage.urls")),
```

开发环境添加 media 文件服务：
```python
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 1.4 迁移和测试

```bash
python manage.py makemigrations core_config core_storage
python manage.py migrate
python -m pytest tests/ -v
```

---

## 任务 2：前端 — 布局壳组件

### 2.1 创建 shell 目录和组件

**创建 `frontend/src/shell/AppLayout.vue`**：

布局容器，包含 Sidebar + TopBar + 主内容区。使用 CSS Grid 或 Flexbox 实现：
- Sidebar 固定宽度（展开 220px / 折叠 60px），高度 100vh
- TopBar 固定高度 52px
- 内容区自适应，带可选背景图和遮罩

```vue
<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <TopBar />
      <main class="content-area" :style="contentStyle">
        <div class="content-overlay">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
```

**创建 `frontend/src/shell/Sidebar.vue`**：

- 从 AppStore 读取 collapsed 状态
- 展开时显示图标+文字，折叠时只显示图标
- 导航菜单项（Sprint 2 先硬编码：首页、设置）
- 底部有折叠/展开按钮

**创建 `frontend/src/shell/TopBar.vue`**：

- 左侧：折叠按钮 + Logo + 面包屑
- 右侧：主题切换按钮 + 用户菜单

**创建 `frontend/src/shell/UserMenu.vue`**：

- 用户头像/名称
- 下拉菜单：设置、退出登录

### 2.2 创建 AppStore

**创建 `frontend/src/stores/app.ts`**：

```typescript
// 状态：sidebarCollapsed, theme, backgroundImage
// 操作：toggleSidebar, setTheme, setBackgroundImage, loadConfig
// 初始化时从 /api/config/ 加载用户配置
```

### 2.3 更新路由

修改 `router/index.ts`：
- `/login` 保持独立（无布局壳）
- `/` 改为嵌套在 AppLayout 下
- 添加 `/settings` 路由

```typescript
{
  path: "/",
  component: AppLayout,
  meta: { requiresAuth: true },
  children: [
    { path: "", name: "home", component: HomeView },
    { path: "settings", name: "settings", component: SettingsView },
  ]
}
```

### 2.4 更新 HomeView

简化为在布局壳内的内容展示，去掉自有的 header 和 logout 按钮。

### 2.5 创建 SettingsView

提供背景图上传区域和主题预览。

---

## 任务 3：前端 — 主题切换 + 背景图

### 3.1 创建 useTheme composable

**创建 `frontend/src/composables/useTheme.ts`**：

- 读取/设置 `document.documentElement.dataset.theme`
- 切换时调用 `/api/config/` 持久化
- 初始化时从 store 读取

### 3.2 背景图系统

- 内容区通过 CSS `background-image` 显示背景图
- 叠加半透明遮罩（`rgba(13,17,23,0.85)`）
- 背景图 URL 存储在 UserConfig 中
- 上传后自动应用

### 3.3 动画与过渡

- Sidebar 折叠/展开使用 `transition: width 0.3s ease`
- 路由切换使用 `<router-view v-slot="{ Component }"><transition><component /></transition></router-view>`
- 主题切换无动画（瞬间切换）

---

## 自检清单

| 检查项 | 覆盖 |
|--------|------|
| 2.1 布局框架 | AppLayout + Sidebar + TopBar |
| 2.2 深色主题 | CSS Variables 已有，AppLayout 使用 |
| 2.3 主题切换 | useTheme + 后端持久化 |
| 2.4 背景图系统 | Storage API + SettingsView |
| 2.5 UX 优化 | transition 动画 |
