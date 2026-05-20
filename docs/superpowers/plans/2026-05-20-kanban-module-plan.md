# 项目看板模块实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 Musk 平台中实现 AI 集成的项目看板模块（kanban），支持任务双轨制、AI 制品产出、依赖管理和制品导出。

**架构：** 遵循 Musk 模块框架规范——独立 SQLite 数据库（`data/kanban.db`），通过 `module_layer` 自动注册和路由。后端 Django+DRF，前端 Vue 3 + Pinia + TypeScript。AI 能力通过 `core.ai` 适配器调用。

**技术栈：** Django 5.x / DRF / SQLite / Vue 3 / Pinia / TypeScript / marked

---

## 文件结构

### 后端（新建）

```
backend/apps/kanban/
├── __init__.py              # 空文件
├── manifest.py              # 模块注册元数据
├── apps.py                  # Django AppConfig
├── models.py                # 5 张数据表
├── serializers.py           # DRF 序列化器
├── views.py                 # API 视图（18 个端点）
├── urls.py                  # URL 路由
├── services/
│   ├── __init__.py          # 空文件
│   └── ai_executor.py       # AI 执行逻辑（prompt 组装 + 调用）
└── migrations/
    └── 0001_initial.py      # 自动生成
```

### 后端（修改）

```
backend/tests/test_kanban.py # 新建测试文件
```

### 前端（新建）

```
frontend/src/
├── stores/kanban.ts                      # Pinia store
├── views/kanban/
│   ├── ProjectListView.vue               # 项目列表页
│   ├── KanbanBoardView.vue               # 看板主视图
│   ├── TaskDetailPanel.vue               # 任务详情面板
│   ├── TaskCard.vue                      # 看板卡片组件
│   ├── CreateTaskDialog.vue              # 创建任务弹窗
│   ├── ContextManager.vue               # 上下文卡片管理弹窗
│   ├── ArtifactEditor.vue               # 制品查看/编辑
│   └── settings/
│       └── KanbanSettingsView.vue        # 设置页
```

### 前端（修改）

```
frontend/src/router/index.ts              # 添加 kanban 路由
```

---

## 任务 1：后端模块脚手架 + 数据模型

**文件：**
- 创建：`backend/apps/kanban/__init__.py`
- 创建：`backend/apps/kanban/manifest.py`
- 创建：`backend/apps/kanban/apps.py`
- 创建：`backend/apps/kanban/models.py`
- 测试：`backend/tests/test_kanban.py`

- [ ] **步骤 1：创建模块目录和空文件**

```bash
mkdir -p backend/apps/kanban/services backend/apps/kanban/migrations
touch backend/apps/kanban/__init__.py backend/apps/kanban/services/__init__.py
```

- [ ] **步骤 2：编写 manifest.py**

```python
# backend/apps/kanban/manifest.py
MANIFEST = {
    "name": "kanban",
    "version": "1.0.0",
    "display_name": "项目看板",
    "icon": "📋",
    "description": "AI 集成的项目看板管理工具",
    "menu_order": 10,
}
```

- [ ] **步骤 3：编写 apps.py**

```python
# backend/apps/kanban/apps.py
from django.apps import AppConfig


class KanbanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.kanban"
    label = "apps_kanban"
    verbose_name = "项目看板"
```

- [ ] **步骤 4：编写 models.py**

```python
# backend/apps/kanban/models.py
from django.db import models


class Project(models.Model):
    """项目。"""
    STATUS_CHOICES = [
        ("active", "活跃"),
        ("archived", "已归档"),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "apps_kanban"
        db_table = "kanban_project"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class ProjectContext(models.Model):
    """项目知识卡片。"""
    CONTENT_TYPE_CHOICES = [
        ("core_info", "核心信息"),
        ("tech_stack", "技术栈"),
        ("architecture", "架构决策"),
        ("custom", "自定义"),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="contexts")
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPE_CHOICES, default="custom")
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "apps_kanban"
        db_table = "kanban_project_context"
        ordering = ["content_type", "title"]

    def __str__(self):
        return f"{self.project.name} - {self.title}"


class Task(models.Model):
    """任务。"""
    TYPE_CHOICES = [
        ("manual", "手动"),
        ("ai", "AI"),
        ("hybrid", "混合"),
    ]
    STATUS_CHOICES = [
        ("todo", "待办"),
        ("ai_running", "AI 执行中"),
        ("review", "待审核"),
        ("in_progress", "进行中"),
        ("done", "已完成"),
        ("cancelled", "已取消"),
    ]
    PRIORITY_CHOICES = [
        ("low", "低"),
        ("medium", "中"),
        ("high", "高"),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="manual")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    ai_prompt = models.TextField(blank=True, default="")
    parent_task = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subtasks")
    position = models.IntegerField(default=0)
    dependencies = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="dependents")
    input_artifacts = models.ManyToManyField("Artifact", blank=True, related_name="referenced_by_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "apps_kanban"
        db_table = "kanban_task"
        ordering = ["position", "-created_at"]

    def __str__(self):
        return self.title


class Artifact(models.Model):
    """制品。"""
    TYPE_CHOICES = [
        ("ai_generated", "AI 生成"),
        ("manual", "手动创建"),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="artifacts")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="artifacts")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default="")
    artifact_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="ai_generated")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "apps_kanban"
        db_table = "kanban_artifact"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class KanbanConfig(models.Model):
    """看板模块配置。"""
    ai_model = models.CharField(max_length=100, default="deepseek-chat")
    ai_system_prompt = models.TextField(default="你是一个项目管理助手。请根据提供的项目上下文和任务要求，产出结构化的文本制品。输出使用 Markdown 格式。")

    class Meta:
        app_label = "apps_kanban"
        db_table = "kanban_config"

    def __str__(self):
        return "KanbanConfig"
```

- [ ] **步骤 5：生成并运行迁移**

```bash
cd backend && python manage.py makemigrations apps_kanban
python manage.py migrate --database=module_kanban
```

预期：迁移成功创建 `kanban_project`、`kanban_project_context`、`kanban_task`、`kanban_artifact`、`kanban_config` 表。注意 M2M 表也会自动创建（`kanban_task_dependencies`、`kanban_task_input_artifacts`）。

- [ ] **步骤 6：编写模型测试**

```python
# backend/tests/test_kanban.py
import pytest
from django.test import TestCase


def _get_db():
    from module_layer.registry import registry
    info = registry.get("kanban")
    return info.db_alias if info else "default"


def _register_client(test_id):
    from rest_framework.test import APIClient
    client = APIClient()
    reg = client.post(
        "/api/auth/register/",
        {"username": f"kanban_{test_id}", "password": "testpass123"},
        format="json",
    )
    token = reg.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db(databases="__all__")
class TestProjectModel(TestCase):
    databases = "__all__"

    def test_create_project(self):
        from apps.kanban.models import Project
        p = Project.objects.using(_get_db()).create(name="测试项目", description="描述")
        assert p.name == "测试项目"
        assert p.status == "active"

    def test_project_status_choices(self):
        from apps.kanban.models import Project
        p = Project.objects.using(_get_db()).create(name="归档项目", status="archived")
        assert p.status == "archived"


@pytest.mark.django_db(databases="__all__")
class TestProjectContextModel(TestCase):
    databases = "__all__"

    def test_create_context(self):
        from apps.kanban.models import Project, ProjectContext
        p = Project.objects.using(_get_db()).create(name="P1")
        ctx = ProjectContext.objects.using(_get_db()).create(
            project=p, content_type="tech_stack",
            title="技术栈", content="Python + Vue"
        )
        assert ctx.content_type == "tech_stack"
        assert ctx.project.name == "P1"


@pytest.mark.django_db(databases="__all__")
class TestTaskModel(TestCase):
    databases = "__all__"

    def test_create_task(self):
        from apps.kanban.models import Project, Task
        p = Project.objects.using(_get_db()).create(name="P1")
        t = Task.objects.using(_get_db()).create(
            project=p, title="设计数据库",
            task_type="ai", priority="high", ai_prompt="请设计数据库模型"
        )
        assert t.task_type == "ai"
        assert t.status == "todo"
        assert t.priority == "high"

    def test_task_dependencies(self):
        from apps.kanban.models import Project, Task
        p = Project.objects.using(_get_db()).create(name="P1")
        t1 = Task.objects.using(_get_db()).create(project=p, title="任务1")
        t2 = Task.objects.using(_get_db()).create(project=p, title="任务2")
        t2.dependencies.add(t1)
        assert t1 in t2.dependencies.all()

    def test_task_subtask(self):
        from apps.kanban.models import Project, Task
        p = Project.objects.using(_get_db()).create(name="P1")
        parent = Task.objects.using(_get_db()).create(project=p, title="父任务")
        child = Task.objects.using(_get_db()).create(project=p, title="子任务", parent_task=parent)
        assert child.parent_task == parent


@pytest.mark.django_db(databases="__all__")
class TestArtifactModel(TestCase):
    databases = "__all__"

    def test_create_artifact(self):
        from apps.kanban.models import Project, Task, Artifact
        p = Project.objects.using(_get_db()).create(name="P1")
        t = Task.objects.using(_get_db()).create(project=p, title="T1")
        a = Artifact.objects.using(_get_db()).create(
            task=t, project=p, title="架构设计文档",
            content="# 数据库设计\n...", artifact_type="ai_generated"
        )
        assert a.artifact_type == "ai_generated"

    def test_task_input_artifacts(self):
        from apps.kanban.models import Project, Task, Artifact
        p = Project.objects.using(_get_db()).create(name="P1")
        t1 = Task.objects.using(_get_db()).create(project=p, title="T1")
        t2 = Task.objects.using(_get_db()).create(project=p, title="T2")
        a = Artifact.objects.using(_get_db()).create(
            task=t1, project=p, title="制品A", content="内容"
        )
        t2.input_artifacts.add(a)
        assert a in t2.input_artifacts.all()


@pytest.mark.django_db(databases="__all__")
class TestKanbanConfigModel(TestCase):
    databases = "__all__"

    def test_create_config(self):
        from apps.kanban.models import KanbanConfig
        cfg = KanbanConfig.objects.using(_get_db()).create(
            ai_model="deepseek-chat",
            ai_system_prompt="你是一个助手"
        )
        assert cfg.ai_model == "deepseek-chat"
```

- [ ] **步骤 7：运行模型测试**

```bash
cd backend && python -m pytest tests/test_kanban.py -v
```

预期：全部 PASS。

- [ ] **步骤 8：Commit**

```bash
git add backend/apps/kanban/ backend/tests/test_kanban.py
git commit -m "feat(kanban): 添加模块脚手架和数据模型"
```

---

## 任务 2：后端序列化器

**文件：**
- 创建：`backend/apps/kanban/serializers.py`
- 修改：`backend/tests/test_kanban.py`

- [ ] **步骤 1：编写序列化器**

```python
# backend/apps/kanban/serializers.py
from rest_framework import serializers
from apps.kanban.models import (
    Project, ProjectContext, Task, Artifact, KanbanConfig,
)


class KanbanConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanConfig
        fields = ("id", "ai_model", "ai_system_prompt")
        read_only_fields = ("id",)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class ProjectContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContext
        fields = ("id", "project", "content_type", "title", "content", "updated_at")
        read_only_fields = ("id", "updated_at")

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return ProjectContext.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = ("id", "task", "project", "title", "content", "artifact_type", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return Artifact.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", default="")
    artifact_count = serializers.SerializerMethodField()
    dependency_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id", "project", "project_name", "title", "description",
            "task_type", "status", "priority", "parent_task", "position",
            "artifact_count", "dependency_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_artifact_count(self, obj):
        return obj.artifacts.count()

    def get_dependency_count(self, obj):
        return obj.dependencies.count()


class TaskDetailSerializer(TaskListSerializer):
    dependencies = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    input_artifacts = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + (
            "ai_prompt", "dependencies", "input_artifacts",
        )

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        dep_ids = validated_data.pop("dependencies", [])
        art_ids = validated_data.pop("input_artifacts", [])
        task = Task.objects.using(using).create(**validated_data)
        if dep_ids:
            deps = Task.objects.using(using).filter(id__in=dep_ids)
            task.dependencies.set(deps)
        if art_ids:
            arts = Artifact.objects.using(using).filter(id__in=art_ids)
            task.input_artifacts.set(arts)
        return task

    def update(self, instance, validated_data):
        validated_data.pop("project_name", None)
        validated_data.pop("artifact_count", None)
        validated_data.pop("dependency_count", None)
        using = validated_data.pop("using", "default")
        dep_ids = validated_data.pop("dependencies", None)
        art_ids = validated_data.pop("input_artifacts", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        if dep_ids is not None:
            deps = Task.objects.using(using).filter(id__in=dep_ids)
            instance.dependencies.set(deps)
        if art_ids is not None:
            arts = Artifact.objects.using(using).filter(id__in=art_ids)
            instance.input_artifacts.set(arts)
        return instance


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    done_count = serializers.SerializerMethodField()
    ai_running_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id", "name", "description", "status",
            "task_count", "done_count", "ai_running_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_done_count(self, obj):
        return obj.tasks.filter(status="done").count()

    def get_ai_running_count(self, obj):
        return obj.tasks.filter(status="ai_running").count()

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return Project.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance
```

- [ ] **步骤 2：运行现有测试确认无回归**

```bash
cd backend && python -m pytest tests/test_kanban.py -v
```

预期：全部 PASS（序列化器尚未被测试使用，但模型测试不应受影响）。

- [ ] **步骤 3：Commit**

```bash
git add backend/apps/kanban/serializers.py
git commit -m "feat(kanban): 添加 DRF 序列化器"
```

---

## 任务 3：后端视图和 URL 路由

**文件：**
- 创建：`backend/apps/kanban/views.py`
- 创建：`backend/apps/kanban/urls.py`
- 修改：`backend/tests/test_kanban.py`（添加 API 测试）

- [ ] **步骤 1：编写 views.py**

```python
# backend/apps/kanban/views.py
import io

from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.kanban.models import (
    Project, ProjectContext, Task, Artifact, KanbanConfig,
)
from apps.kanban.serializers import (
    ProjectSerializer, ProjectContextSerializer,
    TaskListSerializer, TaskDetailSerializer,
    ArtifactSerializer, KanbanConfigSerializer,
)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("kanban")
    return info.db_alias if info else "default"


# ── 项目 ──


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=_get_db())


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


# ── 项目上下文 ──


class ProjectContextListView(generics.ListCreateAPIView):
    serializer_class = ProjectContextSerializer

    def get_queryset(self):
        return ProjectContext.objects.using(_get_db()).filter(
            project_id=self.kwargs["project_pk"]
        )

    def perform_create(self, serializer):
        db = _get_db()
        project = Project.objects.using(db).get(pk=self.kwargs["project_pk"])
        serializer.save(using=db, project=project)


class ProjectContextDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectContextSerializer

    def get_queryset(self):
        return ProjectContext.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


# ── 任务 ──


class TaskListView(generics.ListCreateAPIView):
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        qs = Task.objects.using(_get_db()).filter(
            project_id=self.kwargs["project_pk"]
        ).select_related("project").prefetch_related("artifacts", "dependencies")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        db = _get_db()
        project = Project.objects.using(db).get(pk=self.kwargs["project_pk"])
        serializer.save(using=db, project=project)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        return Task.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


class TaskExecuteView(APIView):
    """触发 AI 执行任务。"""

    def post(self, request, pk):
        db = _get_db()
        try:
            task = Task.objects.using(db).get(pk=pk)
        except Task.DoesNotExist:
            return Response({"detail": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)

        if task.task_type not in ("ai", "hybrid"):
            return Response({"detail": "仅 AI 或混合类型任务可执行"}, status=status.HTTP_400_BAD_REQUEST)

        if task.status != "todo":
            return Response({"detail": f"当前状态 {task.status} 不可执行"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查前置依赖
        unfinished = task.dependencies.exclude(status="done")
        if unfinished.exists():
            names = ", ".join(t.title for t in unfinished[:3])
            return Response(
                {"detail": f"前置依赖未完成: {names}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.kanban.services.ai_executor import execute_ai_task
        try:
            artifact = execute_ai_task(task)
            return Response(ArtifactSerializer(artifact).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": f"AI 执行失败: {str(e)[:200]}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaskStatusView(APIView):
    """快捷状态变更。"""

    def patch(self, request, pk):
        db = _get_db()
        try:
            task = Task.objects.using(db).get(pk=pk)
        except Task.DoesNotExist:
            return Response({"detail": "任务不存在"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        valid_transitions = {
            "todo": ["ai_running", "in_progress", "cancelled"],
            "ai_running": ["review", "todo"],
            "review": ["done", "in_progress", "todo"],
            "in_progress": ["done", "todo", "cancelled"],
            "done": ["todo"],
            "cancelled": ["todo"],
        }
        allowed = valid_transitions.get(task.status, [])
        if new_status not in allowed:
            return Response(
                {"detail": f"不允许从 {task.status} 变更为 {new_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = new_status
        task.save(using=db)
        return Response(TaskDetailSerializer(task).data)


# ── 制品 ──


class TaskArtifactListView(generics.ListCreateAPIView):
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        return Artifact.objects.using(_get_db()).filter(
            task_id=self.kwargs["task_pk"]
        )

    def perform_create(self, serializer):
        db = _get_db()
        task = Task.objects.using(db).get(pk=self.kwargs["task_pk"])
        serializer.save(using=db, task=task, project=task.project)


class ProjectArtifactListView(generics.ListAPIView):
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        return Artifact.objects.using(_get_db()).filter(
            project_id=self.kwargs["project_pk"]
        )


class ArtifactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ArtifactSerializer

    def get_queryset(self):
        return Artifact.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


class ArtifactExportView(APIView):
    """导出单个制品为 MD 文件。"""

    def get(self, request, pk):
        db = _get_db()
        try:
            artifact = Artifact.objects.using(db).select_related("task").get(pk=pk)
        except Artifact.DoesNotExist:
            return Response({"detail": "制品不存在"}, status=status.HTTP_404_NOT_FOUND)

        filename = f"{artifact.task.title[:30]}-{artifact.title[:30]}.md"
        buf = io.BytesIO(artifact.content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf, as_attachment=True, filename=filename,
            content_type="text/markdown",
        )


class ProjectArtifactExportView(APIView):
    """导出项目全部制品为一个 MD 文件。"""

    def get(self, request, project_pk):
        db = _get_db()
        project = Project.objects.using(db).get(pk=project_pk)
        artifacts = (
            Artifact.objects.using(db)
            .filter(project=project)
            .select_related("task")
            .order_by("task_id", "-created_at")
        )

        parts = [f"# {project.name} — 全部制品\n\n"]
        current_task_id = None
        for a in artifacts:
            if a.task_id != current_task_id:
                current_task_id = a.task_id
                parts.append(f"## 任务: {a.task.title}\n\n")
            parts.append(f"### 制品: {a.title}\n\n{a.content}\n\n")

        content = "".join(parts)
        filename = f"{project.name[:30]}-全部制品.md"
        buf = io.BytesIO(content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf, as_attachment=True, filename=filename,
            content_type="text/markdown",
        )


# ── 配置 ──


class KanbanConfigView(APIView):
    """获取/更新看板配置。"""

    def get(self, request):
        db = _get_db()
        config, _ = KanbanConfig.objects.using(db).get_or_create(
            pk=1,
            defaults={
                "ai_model": "deepseek-chat",
                "ai_system_prompt": "你是一个项目管理助手。请根据提供的项目上下文和任务要求，产出结构化的文本制品。输出使用 Markdown 格式。",
            },
        )
        return Response(KanbanConfigSerializer(config).data)

    def patch(self, request):
        db = _get_db()
        config, _ = KanbanConfig.objects.using(db).get_or_create(pk=1, defaults={
            "ai_model": "deepseek-chat",
            "ai_system_prompt": "你是一个项目管理助手。请根据提供的项目上下文和任务要求，产出结构化的文本制品。输出使用 Markdown 格式。",
        })
        serializer = KanbanConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(using=db)
        return Response(serializer.data)
```

- [ ] **步骤 2：编写 urls.py**

```python
# backend/apps/kanban/urls.py
from django.urls import path
from apps.kanban.views import (
    ProjectListCreateView, ProjectDetailView,
    ProjectContextListView, ProjectContextDetailView,
    TaskListView, TaskDetailView, TaskExecuteView, TaskStatusView,
    TaskArtifactListView, ProjectArtifactListView,
    ArtifactDetailView, ArtifactExportView, ProjectArtifactExportView,
    KanbanConfigView,
)

urlpatterns = [
    # 项目
    path("projects/", ProjectListCreateView.as_view(), name="kanban-projects"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="kanban-project-detail"),
    # 项目上下文
    path("projects/<int:project_pk>/contexts/", ProjectContextListView.as_view(), name="kanban-project-contexts"),
    path("contexts/<int:pk>/", ProjectContextDetailView.as_view(), name="kanban-context-detail"),
    # 任务
    path("projects/<int:project_pk>/tasks/", TaskListView.as_view(), name="kanban-tasks"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="kanban-task-detail"),
    path("tasks/<int:pk>/execute/", TaskExecuteView.as_view(), name="kanban-task-execute"),
    path("tasks/<int:pk>/status/", TaskStatusView.as_view(), name="kanban-task-status"),
    # 制品
    path("tasks/<int:task_pk>/artifacts/", TaskArtifactListView.as_view(), name="kanban-task-artifacts"),
    path("projects/<int:project_pk>/artifacts/", ProjectArtifactListView.as_view(), name="kanban-project-artifacts"),
    path("artifacts/<int:pk>/", ArtifactDetailView.as_view(), name="kanban-artifact-detail"),
    path("artifacts/<int:pk>/export/", ArtifactExportView.as_view(), name="kanban-artifact-export"),
    path("projects/<int:project_pk>/artifacts/export/", ProjectArtifactExportView.as_view(), name="kanban-project-artifacts-export"),
    # 配置
    path("config/", KanbanConfigView.as_view(), name="kanban-config"),
]
```

- [ ] **步骤 3：编写 API 测试（追加到 test_kanban.py）**

```python
# 追加到 backend/tests/test_kanban.py 末尾

# ── API 测试 ──


@pytest.mark.django_db(databases="__all__")
class TestProjectAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_list_projects_empty(self):
        resp = self.client.get("/api/kanban/projects/", format="json")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_project(self):
        resp = self.client.post(
            "/api/kanban/projects/",
            {"name": "测试项目", "description": "描述"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "测试项目"

    def test_update_project(self):
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        pk = p.json()["id"]
        resp = self.client.patch(
            f"/api/kanban/projects/{pk}/",
            {"description": "新描述"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "新描述"

    def test_delete_project(self):
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        pk = p.json()["id"]
        resp = self.client.delete(f"/api/kanban/projects/{pk}/")
        assert resp.status_code == 204


@pytest.mark.django_db(databases="__all__")
class TestContextAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        self.project_id = p.json()["id"]

    def test_create_context(self):
        resp = self.client.post(
            f"/api/kanban/projects/{self.project_id}/contexts/",
            {"content_type": "tech_stack", "title": "技术栈", "content": "Python"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "技术栈"

    def test_list_contexts(self):
        self.client.post(
            f"/api/kanban/projects/{self.project_id}/contexts/",
            {"title": "C1"}, format="json",
        )
        resp = self.client.get(
            f"/api/kanban/projects/{self.project_id}/contexts/", format="json"
        )
        assert len(resp.json()) == 1


@pytest.mark.django_db(databases="__all__")
class TestTaskAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        self.project_id = p.json()["id"]

    def test_create_task(self):
        resp = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "设计数据库", "task_type": "ai", "priority": "high", "ai_prompt": "请设计数据库模型"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["task_type"] == "ai"

    def test_list_tasks(self):
        self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "T1"}, format="json",
        )
        resp = self.client.get(
            f"/api/kanban/projects/{self.project_id}/tasks/", format="json"
        )
        assert len(resp.json()) == 1

    def test_update_task_status(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "T1", "task_type": "manual"},
            format="json",
        )
        pk = t.json()["id"]
        resp = self.client.patch(
            f"/api/kanban/tasks/{pk}/status/",
            {"status": "in_progress"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_invalid_status_transition(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "T1", "task_type": "manual"},
            format="json",
        )
        pk = t.json()["id"]
        resp = self.client.patch(
            f"/api/kanban/tasks/{pk}/status/",
            {"status": "done"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db(databases="__all__")
class TestArtifactAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        self.project_id = p.json()["id"]
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "T1"}, format="json",
        )
        self.task_id = t.json()["id"]

    def test_create_artifact(self):
        resp = self.client.post(
            f"/api/kanban/tasks/{self.task_id}/artifacts/",
            {"title": "文档", "content": "# 内容", "artifact_type": "manual"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "文档"

    def test_export_artifact(self):
        self.client.post(
            f"/api/kanban/tasks/{self.task_id}/artifacts/",
            {"title": "文档", "content": "# 内容", "artifact_type": "manual"},
            format="json",
        )
        artifacts = self.client.get(
            f"/api/kanban/tasks/{self.task_id}/artifacts/", format="json"
        ).json()
        pk = artifacts[0]["id"]
        resp = self.client.get(f"/api/kanban/artifacts/{pk}/export/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/markdown"

    def test_export_project_artifacts(self):
        self.client.post(
            f"/api/kanban/tasks/{self.task_id}/artifacts/",
            {"title": "文档", "content": "# 内容"}, format="json",
        )
        resp = self.client.get(
            f"/api/kanban/projects/{self.project_id}/artifacts/export/"
        )
        assert resp.status_code == 200


@pytest.mark.django_db(databases="__all__")
class TestKanbanConfigAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())

    def test_get_config_defaults(self):
        resp = self.client.get("/api/kanban/config/", format="json")
        assert resp.status_code == 200
        assert resp.json()["ai_model"] == "deepseek-chat"

    def test_update_config(self):
        resp = self.client.patch(
            "/api/kanban/config/",
            {"ai_model": "glm-4-plus"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["ai_model"] == "glm-4-plus"
```

- [ ] **步骤 4：运行全部测试**

```bash
cd backend && python -m pytest tests/test_kanban.py -v
```

预期：所有模型测试 + API 测试 PASS。

- [ ] **步骤 5：运行全部项目测试确认无回归**

```bash
cd backend && python -m pytest tests/ -v
```

预期：所有测试 PASS（包含原有 blog 测试和新增 kanban 测试）。

- [ ] **步骤 6：Commit**

```bash
git add backend/apps/kanban/views.py backend/apps/kanban/urls.py backend/tests/test_kanban.py
git commit -m "feat(kanban): 添加视图、URL 路由和 API 测试"
```

---

## 任务 4：AI 执行服务

**文件：**
- 创建：`backend/apps/kanban/services/ai_executor.py`
- 修改：`backend/tests/test_kanban.py`（添加 AI 执行测试）

- [ ] **步骤 1：编写 AI 执行服务**

```python
# backend/apps/kanban/services/ai_executor.py
"""AI 任务执行服务。"""

import logging

from apps.kanban.models import Task, Artifact, KanbanConfig, ProjectContext

logger = logging.getLogger(__name__)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("kanban")
    return info.db_alias if info else "default"


def _call_ai(messages: list, model_name: str = None) -> str:
    """调用 AI 模型，返回文本响应。"""
    from core.ai.adapters import get_adapter
    adapter = get_adapter(model_name)
    return adapter.chat(messages, stream=False)


def _get_config() -> KanbanConfig:
    db = _get_db()
    config, _ = KanbanConfig.objects.using(db).get_or_create(
        pk=1,
        defaults={
            "ai_model": "deepseek-chat",
            "ai_system_prompt": "你是一个项目管理助手。请根据提供的项目上下文和任务要求，产出结构化的文本制品。输出使用 Markdown 格式。",
        },
    )
    return config


def _build_prompt(task: Task) -> list[dict]:
    """组装 AI prompt。"""
    db = _get_db()
    config = _get_config()
    messages = []

    # 1. 系统指令
    messages.append({"role": "system", "content": config.ai_system_prompt})

    # 2. 组装用户消息
    parts = []

    # 项目上下文
    contexts = ProjectContext.objects.using(db).filter(project=task.project)
    if contexts.exists():
        parts.append("## 项目上下文\n")
        for ctx in contexts:
            parts.append(f"### {ctx.title}（{ctx.get_content_type_display()}）\n{ctx.content}\n")
        parts.append("")

    # 上游制品引用
    input_arts = task.input_artifacts.all()
    if input_arts.exists():
        parts.append("## 上游制品引用\n")
        for art in input_arts:
            parts.append(f"### {art.title}（来自任务: {art.task.title}）\n{art.content}\n")
        parts.append("")

    # 依赖任务摘要
    deps = task.dependencies.all()
    if deps.exists():
        parts.append("## 前置依赖任务\n")
        for dep in deps:
            latest_art = dep.artifacts.first()
            summary = latest_art.content[:200] if latest_art else "无制品"
            parts.append(f"- {dep.title}（状态: {dep.get_status_display()}，最新制品摘要: {summary}）\n")
        parts.append("")

    # 任务自身 prompt
    parts.append("## 任务要求\n")
    parts.append(task.ai_prompt)

    messages.append({"role": "user", "content": "\n".join(parts)})
    return messages


def execute_ai_task(task: Task) -> Artifact:
    """执行 AI 任务，返回生成的制品。"""
    db = _get_db()
    config = _get_config()

    # 状态变更为 AI 执行中
    task.status = "ai_running"
    task.save(using=db)

    try:
        messages = _build_prompt(task)
        response_text = _call_ai(messages, model_name=config.ai_model)

        # 写入制品
        artifact = Artifact.objects.using(db).create(
            task=task,
            project=task.project,
            title=f"{task.title} - AI 产出",
            content=response_text,
            artifact_type="ai_generated",
        )

        # 状态变更为待审核
        task.status = "review"
        task.save(using=db)

        return artifact

    except Exception as e:
        logger.error("AI 执行失败 task=%s: %s", task.id, e)
        task.status = "todo"
        task.save(using=db)
        raise
```

- [ ] **步骤 2：编写 AI 执行测试（追加到 test_kanban.py）**

```python
# 追加到 backend/tests/test_kanban.py 末尾

from unittest.mock import patch, MagicMock

# ── AI 执行测试 ──


@pytest.mark.django_db(databases="__all__")
class TestTaskExecuteAPI(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = _register_client(self.id())
        p = self.client.post(
            "/api/kanban/projects/", {"name": "P1"}, format="json"
        )
        self.project_id = p.json()["id"]
        # 创建上下文
        self.client.post(
            f"/api/kanban/projects/{self.project_id}/contexts/",
            {"title": "技术栈", "content_type": "tech_stack", "content": "Python + Django"},
            format="json",
        )

    def test_execute_ai_task_success(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "设计API", "task_type": "ai", "ai_prompt": "请设计 REST API"},
            format="json",
        )
        task_id = t.json()["id"]

        with patch("apps.kanban.services.ai_executor._call_ai") as mock_ai:
            mock_ai.return_value = "# API 设计\n\n## 端点列表\n..."
            resp = self.client.post(
                f"/api/kanban/tasks/{task_id}/execute/", format="json"
            )
        assert resp.status_code == 201
        assert "AI 产出" in resp.json()["title"]

        # 验证任务状态变为 review
        task_resp = self.client.get(f"/api/kanban/tasks/{task_id}/", format="json")
        assert task_resp.json()["status"] == "review"

    def test_execute_manual_task_rejected(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "手动任务", "task_type": "manual"},
            format="json",
        )
        task_id = t.json()["id"]
        resp = self.client.post(
            f"/api/kanban/tasks/{task_id}/execute/", format="json"
        )
        assert resp.status_code == 400

    def test_execute_with_unfinished_dependency(self):
        t1 = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "前置任务", "task_type": "manual"},
            format="json",
        )
        t1_id = t1.json()["id"]

        t2 = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "后续任务", "task_type": "ai", "ai_prompt": "测试", "dependencies": [t1_id]},
            format="json",
        )
        t2_id = t2.json()["id"]

        resp = self.client.post(
            f"/api/kanban/tasks/{t2_id}/execute/", format="json"
        )
        assert resp.status_code == 400
        assert "前置依赖" in resp.json()["detail"]

    def test_execute_ai_failure_rollback(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "AI任务", "task_type": "ai", "ai_prompt": "测试"},
            format="json",
        )
        task_id = t.json()["id"]

        with patch("apps.kanban.services.ai_executor._call_ai") as mock_ai:
            mock_ai.side_effect = Exception("API timeout")
            resp = self.client.post(
                f"/api/kanban/tasks/{task_id}/execute/", format="json"
            )
        assert resp.status_code == 500

        # 验证状态回退为 todo
        task_resp = self.client.get(f"/api/kanban/tasks/{task_id}/", format="json")
        assert task_resp.json()["status"] == "todo"

    def test_hybrid_task_full_flow(self):
        t = self.client.post(
            f"/api/kanban/projects/{self.project_id}/tasks/",
            {"title": "混合任务", "task_type": "hybrid", "ai_prompt": "设计方案"},
            format="json",
        )
        task_id = t.json()["id"]

        with patch("apps.kanban.services.ai_executor._call_ai") as mock_ai:
            mock_ai.return_value = "# 设计方案\n..."
            self.client.post(f"/api/kanban/tasks/{task_id}/execute/", format="json")

        # 审核通过 → 进行中
        resp = self.client.patch(
            f"/api/kanban/tasks/{task_id}/status/",
            {"status": "in_progress"}, format="json",
        )
        assert resp.status_code == 200

        # 完成
        resp = self.client.patch(
            f"/api/kanban/tasks/{task_id}/status/",
            {"status": "done"}, format="json",
        )
        assert resp.status_code == 200
```

- [ ] **步骤 3：运行全部测试**

```bash
cd backend && python -m pytest tests/test_kanban.py -v
```

预期：全部 PASS。

- [ ] **步骤 4：运行全部项目测试确认无回归**

```bash
cd backend && python -m pytest tests/ -v
```

预期：全部 PASS。

- [ ] **步骤 5：Commit**

```bash
git add backend/apps/kanban/services/ai_executor.py backend/tests/test_kanban.py
git commit -m "feat(kanban): 添加 AI 执行服务和测试"
```

---

## 任务 5：前端 Store

**文件：**
- 创建：`frontend/src/stores/kanban.ts`

- [ ] **步骤 1：编写 Pinia store**

```typescript
// frontend/src/stores/kanban.ts
import { ref } from "vue";
import api from "@/core/api";

// ── 类型定义 ──

export interface Project {
  id: number;
  name: string;
  description: string;
  status: "active" | "archived";
  task_count: number;
  done_count: number;
  ai_running_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectContext {
  id: number;
  project: number;
  content_type: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface Task {
  id: number;
  project: number;
  project_name: string;
  title: string;
  description: string;
  task_type: "manual" | "ai" | "hybrid";
  status: "todo" | "ai_running" | "review" | "in_progress" | "done" | "cancelled";
  priority: "low" | "medium" | "high";
  ai_prompt: string;
  parent_task: number | null;
  position: number;
  dependencies: number[];
  input_artifacts: number[];
  artifact_count: number;
  dependency_count: number;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: number;
  task: number;
  project: number;
  title: string;
  content: string;
  artifact_type: "ai_generated" | "manual";
  created_at: string;
}

export interface KanbanConfig {
  id: number;
  ai_model: string;
  ai_system_prompt: string;
}

// ── Store ──

export const useKanbanStore = defineStore("kanban", () => {
  const projects = ref<Project[]>([]);
  const currentProject = ref<Project | null>(null);
  const tasks = ref<Task[]>([]);
  const currentTask = ref<Task | null>(null);
  const artifacts = ref<Artifact[]>([]);
  const contexts = ref<ProjectContext[]>([]);
  const config = ref<KanbanConfig | null>(null);
  const loading = ref(false);

  // ── 项目 ──

  async function fetchProjects() {
    const { data } = await api.get("/kanban/projects/");
    projects.value = data;
  }

  async function fetchProject(id: number) {
    const { data } = await api.get(`/kanban/projects/${id}/`);
    currentProject.value = data;
  }

  async function createProject(payload: Partial<Project>) {
    const { data } = await api.post("/kanban/projects/", payload);
    projects.value.unshift(data);
    return data;
  }

  async function updateProject(id: number, payload: Partial<Project>) {
    const { data } = await api.patch(`/kanban/projects/${id}/`, payload);
    if (currentProject.value?.id === id) currentProject.value = data;
    const idx = projects.value.findIndex((p) => p.id === id);
    if (idx !== -1) projects.value[idx] = data;
    return data;
  }

  async function deleteProject(id: number) {
    await api.delete(`/kanban/projects/${id}/`);
    projects.value = projects.value.filter((p) => p.id !== id);
  }

  // ── 上下文 ──

  async function fetchContexts(projectId: number) {
    const { data } = await api.get(`/kanban/projects/${projectId}/contexts/`);
    contexts.value = data;
  }

  async function createContext(projectId: number, payload: Partial<ProjectContext>) {
    const { data } = await api.post(`/kanban/projects/${projectId}/contexts/`, payload);
    contexts.value.push(data);
    return data;
  }

  async function updateContext(id: number, payload: Partial<ProjectContext>) {
    const { data } = await api.patch(`/kanban/contexts/${id}/`, payload);
    const idx = contexts.value.findIndex((c) => c.id === id);
    if (idx !== -1) contexts.value[idx] = data;
    return data;
  }

  async function deleteContext(id: number) {
    await api.delete(`/kanban/contexts/${id}/`);
    contexts.value = contexts.value.filter((c) => c.id !== id);
  }

  // ── 任务 ──

  async function fetchTasks(projectId: number, params?: Record<string, string>) {
    const { data } = await api.get(`/kanban/projects/${projectId}/tasks/`, { params });
    tasks.value = data;
  }

  async function fetchTask(id: number) {
    const { data } = await api.get(`/kanban/tasks/${id}/`);
    currentTask.value = data;
    return data;
  }

  async function createTask(projectId: number, payload: Partial<Task>) {
    const { data } = await api.post(`/kanban/projects/${projectId}/tasks/`, payload);
    tasks.value.push(data);
    return data;
  }

  async function updateTask(id: number, payload: Partial<Task>) {
    const { data } = await api.patch(`/kanban/tasks/${id}/`, payload);
    if (currentTask.value?.id === id) currentTask.value = data;
    const idx = tasks.value.findIndex((t) => t.id === id);
    if (idx !== -1) tasks.value[idx] = data;
    return data;
  }

  async function deleteTask(id: number) {
    await api.delete(`/kanban/tasks/${id}/`);
    tasks.value = tasks.value.filter((t) => t.id !== id);
    if (currentTask.value?.id === id) currentTask.value = null;
  }

  async function executeTask(id: number) {
    const { data } = await api.post(`/kanban/tasks/${id}/execute/`);
    // 刷新任务状态
    await fetchTask(id);
    return data;
  }

  async function updateTaskStatus(id: number, newStatus: string) {
    const { data } = await api.patch(`/kanban/tasks/${id}/status/`, { status: newStatus });
    if (currentTask.value?.id === id) currentTask.value = data;
    const idx = tasks.value.findIndex((t) => t.id === id);
    if (idx !== -1) tasks.value[idx] = data;
    return data;
  }

  // ── 制品 ──

  async function fetchTaskArtifacts(taskId: number) {
    const { data } = await api.get(`/kanban/tasks/${taskId}/artifacts/`);
    artifacts.value = data;
  }

  async function fetchProjectArtifacts(projectId: number) {
    const { data } = await api.get(`/kanban/projects/${projectId}/artifacts/`);
    artifacts.value = data;
  }

  async function createArtifact(taskId: number, payload: Partial<Artifact>) {
    const { data } = await api.post(`/kanban/tasks/${taskId}/artifacts/`, payload);
    artifacts.value.push(data);
    return data;
  }

  async function updateArtifact(id: number, payload: Partial<Artifact>) {
    const { data } = await api.patch(`/kanban/artifacts/${id}/`, payload);
    const idx = artifacts.value.findIndex((a) => a.id === id);
    if (idx !== -1) artifacts.value[idx] = data;
    return data;
  }

  async function deleteArtifact(id: number) {
    await api.delete(`/kanban/artifacts/${id}/`);
    artifacts.value = artifacts.value.filter((a) => a.id !== id);
  }

  function getArtifactExportUrl(id: number) {
    return `/api/kanban/artifacts/${id}/export/`;
  }

  function getProjectExportUrl(projectId: number) {
    return `/api/kanban/projects/${projectId}/artifacts/export/`;
  }

  // ── 配置 ──

  async function fetchConfig() {
    const { data } = await api.get("/kanban/config/");
    config.value = data;
  }

  async function updateConfig(payload: Partial<KanbanConfig>) {
    const { data } = await api.patch("/kanban/config/", payload);
    config.value = data;
    return data;
  }

  return {
    projects, currentProject, tasks, currentTask, artifacts,
    contexts, config, loading,
    fetchProjects, fetchProject, createProject, updateProject, deleteProject,
    fetchContexts, createContext, updateContext, deleteContext,
    fetchTasks, fetchTask, createTask, updateTask, deleteTask,
    executeTask, updateTaskStatus,
    fetchTaskArtifacts, fetchProjectArtifacts, createArtifact,
    updateArtifact, deleteArtifact, getArtifactExportUrl, getProjectExportUrl,
    fetchConfig, updateConfig,
  };
});
```

- [ ] **步骤 2：验证 TypeScript 编译**

```bash
cd frontend && npx vue-tsc --noEmit --pretty 2>&1 | head -20
```

预期：无 kanban store 相关的编译错误（可能有 router 中尚未定义路由的引用错误，在任务 6 中修复）。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/stores/kanban.ts
git commit -m "feat(kanban): 添加 Pinia store 和类型定义"
```

---

## 任务 6：前端路由 + 项目列表页

**文件：**
- 修改：`frontend/src/router/index.ts`
- 创建：`frontend/src/views/kanban/ProjectListView.vue`

- [ ] **步骤 1：在 router/index.ts 中添加 kanban 路由**

在 blog 路由块之后追加：

```typescript
// 在 blog 的 children 数组之后添加
{
  path: "kanban",
  children: [
    { path: "", name: "kanban", component: () => import("@/views/kanban/ProjectListView.vue") },
    { path: "settings", name: "kanban-settings", component: () => import("@/views/kanban/settings/KanbanSettingsView.vue") },
    { path: ":projectId", name: "kanban-board", component: () => import("@/views/kanban/KanbanBoardView.vue") },
  ],
},
```

- [ ] **步骤 2：编写项目列表页**

```vue
<!-- frontend/src/views/kanban/ProjectListView.vue -->
<template>
  <div class="project-list">
    <div class="list-header">
      <h1>项目看板</h1>
      <div class="header-actions">
        <button class="settings-btn" @click="router.push('/kanban/settings')">⚙ 设置</button>
        <button class="add-btn" @click="showCreate = true">+ 新建项目</button>
      </div>
    </div>

    <div v-if="kanbanStore.projects.length === 0" class="empty">
      <p>暂无项目</p>
      <p class="empty-hint">点击"新建项目"开始管理你的任务</p>
    </div>
    <div v-else class="project-grid">
      <div
        v-for="p in kanbanStore.projects" :key="p.id"
        class="project-card"
        @click="router.push(`/kanban/${p.id}`)"
      >
        <div class="card-title">{{ p.name }}</div>
        <div v-if="p.description" class="card-desc">{{ p.description }}</div>
        <div class="card-stats">
          <span>{{ p.task_count }} 任务</span>
          <span>{{ p.done_count }} 完成</span>
          <span v-if="p.ai_running_count">🤖 {{ p.ai_running_count }} AI执行中</span>
        </div>
        <div v-if="p.task_count > 0" class="progress-bar">
          <div class="progress-fill" :style="{ width: `${(p.done_count / p.task_count) * 100}%` }"></div>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="dialog-overlay" @click.self="showCreate = false">
      <div class="dialog">
        <h3>新建项目</h3>
        <input v-model="newName" class="dialog-input" placeholder="项目名称" @keydown.enter="handleCreate" />
        <textarea v-model="newDesc" class="dialog-textarea" placeholder="项目描述（可选）" rows="3" />
        <div class="dialog-actions">
          <button class="btn-cancel" @click="showCreate = false">取消</button>
          <button class="btn-primary" @click="handleCreate" :disabled="!newName.trim()">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useKanbanStore } from "@/stores/kanban";

const router = useRouter();
const kanbanStore = useKanbanStore();
const showCreate = ref(false);
const newName = ref("");
const newDesc = ref("");

onMounted(() => {
  kanbanStore.fetchProjects();
});

async function handleCreate() {
  if (!newName.value.trim()) return;
  await kanbanStore.createProject({ name: newName.value.trim(), description: newDesc.value.trim() });
  newName.value = "";
  newDesc.value = "";
  showCreate.value = false;
}
</script>

<style scoped>
.project-list { padding: 0 0 24px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.list-header h1 { font-size: 24px; color: var(--text-primary); }
.header-actions { display: flex; gap: 8px; }
.settings-btn {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 13px;
}
.settings-btn:hover { border-color: var(--accent); color: var(--accent); }
.add-btn {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.project-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.project-card {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 16px; cursor: pointer; transition: all 0.2s;
}
.project-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: var(--card-shadow); }
.card-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.card-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.card-stats { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }
.progress-bar { height: 4px; background: var(--bg-tertiary, #21262d); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #3fb950; border-radius: 2px; transition: width 0.3s; }
.empty { text-align: center; padding: 60px 0; color: var(--text-secondary); }
.empty-hint { font-size: 13px; color: var(--text-muted); margin-top: 8px; }
/* Dialog */
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg); padding: 24px; width: 480px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; color: var(--text-primary); }
.dialog-input, .dialog-textarea {
  width: 100%; padding: 10px 12px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 14px; margin-bottom: 12px; font-family: inherit; resize: vertical;
}
.dialog-input:focus, .dialog-textarea:focus { border-color: var(--input-focus-border, var(--accent)); outline: none; }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer;
}
.btn-primary {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

- [ ] **步骤 3：创建占位文件确保路由不报错**

创建空的占位组件（在后续任务中填充内容）：

```bash
mkdir -p frontend/src/views/kanban/settings
touch frontend/src/views/kanban/KanbanBoardView.vue
touch frontend/src/views/kanban/settings/KanbanSettingsView.vue
```

`KanbanBoardView.vue` 占位内容：

```vue
<template>
  <div style="padding:24px; color:var(--text-secondary);">看板视图（待实现）</div>
</template>
```

`KanbanSettingsView.vue` 占位内容：

```vue
<template>
  <div style="padding:24px; color:var(--text-secondary);">看板设置（待实现）</div>
</template>
```

- [ ] **步骤 4：验证前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功，无编译错误。

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/router/index.ts frontend/src/views/kanban/ frontend/src/stores/kanban.ts
git commit -m "feat(kanban): 添加前端路由、项目列表页和 store"
```

---

## 任务 7：看板主视图

**文件：**
- 创建：`frontend/src/views/kanban/KanbanBoardView.vue`
- 创建：`frontend/src/views/kanban/TaskCard.vue`
- 创建：`frontend/src/views/kanban/CreateTaskDialog.vue`

- [ ] **步骤 1：编写 TaskCard 组件**

```vue
<!-- frontend/src/views/kanban/TaskCard.vue -->
<template>
  <div :class="['task-card', `priority-${task.priority}`, `status-${task.status}`]" @click="$emit('click')">
    <div class="card-title">{{ task.title }}</div>
    <div class="card-tags">
      <span :class="['type-tag', `type-${task.task_type}`]">{{ typeLabel }}</span>
      <span v-if="task.priority === 'high'" class="priority-tag">高</span>
    </div>
    <div v-if="task.dependency_count > 0" class="card-deps">
      🔗 {{ task.dependency_count }} 个依赖
    </div>
    <div v-if="task.artifact_count > 0" class="card-artifacts">
      📎 {{ task.artifact_count }} 个制品
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Task } from "@/stores/kanban";

const props = defineProps<{ task: Task }>();
defineEmits<{ click: [] }>();

const typeLabel = computed(() => {
  const map: Record<string, string> = { manual: "✋ 手动", ai: "🤖 AI", hybrid: "🔀 混合" };
  return map[props.task.task_type] || props.task.task_type;
});
</script>

<style scoped>
.task-card {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-sm); padding: 10px 12px; cursor: pointer;
  transition: all 0.15s; margin-bottom: 6px;
}
.task-card:hover { border-color: var(--accent); }
.task-card.status-done { opacity: 0.5; }
.task-card.priority-high { border-left: 3px solid #f85149; }
.card-title { font-size: 13px; color: var(--text-primary); font-weight: 500; margin-bottom: 6px; line-height: 1.4; }
.card-tags { display: flex; gap: 6px; }
.type-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 8px;
}
.type-manual { background: rgba(110,118,129,0.15); color: #8b949e; }
.type-ai { background: rgba(88,166,255,0.15); color: #58a6ff; }
.type-hybrid { background: rgba(188,140,255,0.15); color: #bc8cff; }
.priority-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 8px;
  background: rgba(248,81,73,0.1); color: #f85149;
}
.card-deps, .card-artifacts { font-size: 10px; color: var(--text-muted); margin-top: 4px; }
</style>
```

- [ ] **步骤 2：编写 CreateTaskDialog 组件**

```vue
<!-- frontend/src/views/kanban/CreateTaskDialog.vue -->
<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>新建任务</h3>
      <input v-model="form.title" class="dialog-input" placeholder="任务标题" />
      <textarea v-model="form.description" class="dialog-textarea" placeholder="任务描述（可选）" rows="3" />
      <div class="form-row">
        <select v-model="form.task_type" class="dialog-select">
          <option value="manual">✋ 手动</option>
          <option value="ai">🤖 AI</option>
          <option value="hybrid">🔀 混合</option>
        </select>
        <select v-model="form.priority" class="dialog-select">
          <option value="low">低优先级</option>
          <option value="medium">中优先级</option>
          <option value="high">高优先级</option>
        </select>
      </div>
      <textarea
        v-if="form.task_type !== 'manual'"
        v-model="form.ai_prompt"
        class="dialog-textarea"
        placeholder="AI Prompt（描述你希望 AI 完成什么）"
        rows="4"
      />
      <div class="dialog-actions">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-primary" @click="handleCreate" :disabled="!form.title.trim()">创建</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";

defineProps<{ visible: boolean }>();
const emit = defineEmits<{ close: []; created: [] }>();

const form = reactive({
  title: "",
  description: "",
  task_type: "manual" as "manual" | "ai" | "hybrid",
  priority: "medium" as "low" | "medium" | "high",
  ai_prompt: "",
});

async function handleCreate() {
  if (!form.title.trim()) return;
  const { useKanbanStore } = await import("@/stores/kanban");
  const { useRoute } = await import("vue-router");
  const kanbanStore = useKanbanStore();
  const route = useRoute();
  const projectId = Number(route.params.projectId);

  await kanbanStore.createTask(projectId, { ...form });
  Object.assign(form, { title: "", description: "", task_type: "manual", priority: "medium", ai_prompt: "" });
  emit("created");
  emit("close");
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg); padding: 24px; width: 520px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; color: var(--text-primary); }
.dialog-input, .dialog-textarea, .dialog-select {
  width: 100%; padding: 10px 12px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 14px; margin-bottom: 12px; font-family: inherit; resize: vertical;
}
.dialog-input:focus, .dialog-textarea:focus, .dialog-select:focus { border-color: var(--input-focus-border, var(--accent)); outline: none; }
.form-row { display: flex; gap: 8px; }
.form-row .dialog-select { flex: 1; }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer;
}
.btn-primary {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

- [ ] **步骤 3：编写 KanbanBoardView 主视图**

```vue
<!-- frontend/src/views/kanban/KanbanBoardView.vue -->
<template>
  <div class="kanban-board">
    <div class="board-header">
      <div class="header-left">
        <button class="back-btn" @click="router.push('/kanban')">← 返回</button>
        <h1>{{ kanbanStore.currentProject?.name || '加载中...' }}</h1>
      </div>
      <div class="header-actions">
        <button class="context-btn" @click="showContext = true">📄 上下文</button>
        <button class="export-btn" @click="handleExportAll">📥 导出全部制品</button>
        <button class="add-btn" @click="showCreateTask = true">+ 添加任务</button>
      </div>
    </div>

    <div class="board-columns">
      <div v-for="col in columns" :key="col.status" :class="['board-column', `col-${col.status}`]">
        <div :class="['column-header', `header-${col.status}`]">
          {{ col.label }} ({{ getTasksByStatus(col.status).length }})
        </div>
        <div class="column-body">
          <TaskCard
            v-for="task in getTasksByStatus(col.status)"
            :key="task.id"
            :task="task"
            @click="openDetail(task.id)"
          />
        </div>
      </div>
    </div>

    <!-- 任务详情面板 -->
    <TaskDetailPanel
      v-if="detailTaskId"
      :task-id="detailTaskId"
      @close="detailTaskId = null"
      @refresh="refreshBoard"
    />

    <CreateTaskDialog :visible="showCreateTask" @close="showCreateTask = false" @created="refreshBoard" />
    <ContextManager :visible="showContext" :project-id="projectId" @close="showContext = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useKanbanStore } from "@/stores/kanban";
import TaskCard from "./TaskCard.vue";
import TaskDetailPanel from "./TaskDetailPanel.vue";
import CreateTaskDialog from "./CreateTaskDialog.vue";
import ContextManager from "./ContextManager.vue";

const route = useRoute();
const router = useRouter();
const kanbanStore = useKanbanStore();
const projectId = Number(route.params.projectId);

const showCreateTask = ref(false);
const showContext = ref(false);
const detailTaskId = ref<number | null>(null);

const columns = [
  { status: "todo", label: "待办" },
  { status: "ai_running", label: "🤖 AI 执行中" },
  { status: "review", label: "⏳ 待审核" },
  { status: "in_progress", label: "🔨 进行中" },
  { status: "done", label: "✅ 已完成" },
];

onMounted(async () => {
  await kanbanStore.fetchProject(projectId);
  await kanbanStore.fetchTasks(projectId);
});

function getTasksByStatus(status: string) {
  return kanbanStore.tasks.filter((t) => t.status === status);
}

function openDetail(id: number) {
  detailTaskId.value = id;
}

async function refreshBoard() {
  await kanbanStore.fetchTasks(projectId);
}

function handleExportAll() {
  const url = kanbanStore.getProjectExportUrl(projectId);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${kanbanStore.currentProject?.name || "项目"}-全部制品.md`;
  a.click();
}
</script>

<style scoped>
.kanban-board { display: flex; flex-direction: column; height: calc(100vh - 52px - 48px); margin: -24px; }
.board-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary); flex-shrink: 0;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.back-btn { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 14px; }
.header-left h1 { font-size: 18px; color: var(--text-primary); }
.header-actions { display: flex; gap: 8px; }
.context-btn, .export-btn {
  padding: 6px 12px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 12px;
}
.context-btn:hover, .export-btn:hover { border-color: var(--accent); color: var(--accent); }
.add-btn {
  padding: 6px 12px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 12px;
}
.board-columns {
  display: flex; gap: 12px; flex: 1; overflow-x: auto;
  padding: 16px 20px; background: var(--bg-primary);
}
.board-column {
  min-width: 240px; flex: 1; display: flex; flex-direction: column;
}
.column-header {
  font-size: 12px; font-weight: 600; padding: 8px 12px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  margin-bottom: 0;
}
.header-todo { color: #8b949e; background: rgba(110,118,129,0.08); }
.header-ai_running { color: #58a6ff; background: rgba(88,166,255,0.06); }
.header-review { color: #d29922; background: rgba(210,153,34,0.06); }
.header-in_progress { color: #bc8cff; background: rgba(188,140,255,0.06); }
.header-done { color: #3fb950; background: rgba(63,185,80,0.06); }
.column-body {
  flex: 1; padding: 8px; overflow-y: auto;
  background: rgba(110,118,129,0.03); border-radius: 0 0 var(--radius-sm) var(--radius-sm);
}
</style>
```

- [ ] **步骤 4：创建 TaskDetailPanel 和 ContextManager 占位组件**

`TaskDetailPanel.vue` 占位：

```vue
<!-- frontend/src/views/kanban/TaskDetailPanel.vue -->
<template>
  <div class="detail-overlay" @click.self="$emit('close')">
    <div class="detail-panel">
      <div class="panel-header">
        <span>任务详情（待实现）</span>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      <div class="panel-body">
        <p style="color:var(--text-secondary); padding:24px;">任务详情面板将在下一步实现</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ taskId: number }>();
defineEmits<{ close: []; refresh: [] }>();
</script>

<style scoped>
.detail-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; justify-content: flex-end; z-index: 50;
}
.detail-panel {
  width: 520px; max-width: 90vw; height: 100%;
  background: var(--bg-secondary); border-left: 1px solid var(--border-primary);
  display: flex; flex-direction: column; overflow-y: auto;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-primary);
  font-size: 14px; color: var(--text-primary); font-weight: 600;
}
.close-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 16px; }
.panel-body { flex: 1; padding: 20px; }
</style>
```

`ContextManager.vue` 占位：

```vue
<!-- frontend/src/views/kanban/ContextManager.vue -->
<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>项目上下文（待实现）</h3>
      <p style="color:var(--text-secondary);">上下文管理将在下一步实现</p>
      <div class="dialog-actions">
        <button class="btn-cancel" @click="$emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean; projectId: number }>();
defineEmits<{ close: [] }>();
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg); padding: 24px; width: 560px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; color: var(--text-primary); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer;
}
</style>
```

- [ ] **步骤 5：验证前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功。

- [ ] **步骤 6：Commit**

```bash
git add frontend/src/views/kanban/
git commit -m "feat(kanban): 添加看板主视图、任务卡片和创建任务弹窗"
```

---

## 任务 8：任务详情面板 + 上下文管理 + 制品编辑

**文件：**
- 重写：`frontend/src/views/kanban/TaskDetailPanel.vue`
- 重写：`frontend/src/views/kanban/ContextManager.vue`
- 创建：`frontend/src/views/kanban/ArtifactEditor.vue`

- [ ] **步骤 1：编写完整的 TaskDetailPanel.vue**

替换任务 7 中的占位内容。核心模板结构：

```vue
<!-- frontend/src/views/kanban/TaskDetailPanel.vue -->
<template>
  <div class="detail-overlay" @click.self="$emit('close')">
    <div class="detail-panel">
      <div class="panel-header">
        <span class="close-btn" @click="$emit('close')">✕</span>
      </div>
      <div v-if="!task" class="loading">加载中...</div>
      <div v-else class="panel-body">
        <!-- 类型 + 状态 -->
        <div class="meta-row">
          <span :class="['type-badge', `type-${task.task_type}`]">{{ typeLabel }}</span>
          <span :class="['status-badge', `status-${task.status}`]">{{ statusLabel }}</span>
          <span class="priority-badge">{{ task.priority }}</span>
        </div>

        <!-- 标题 -->
        <div class="field-group">
          <label>标题</label>
          <input v-if="editing" v-model="form.title" class="field-input" />
          <h2 v-else class="task-title editable" @click="startEdit">{{ task.title }}</h2>
        </div>

        <!-- 描述 -->
        <div class="field-group">
          <label>描述</label>
          <textarea v-if="editing" v-model="form.description" class="field-textarea" rows="3" />
          <div v-else class="field-content editable" @click="startEdit">
            {{ task.description || '点击编辑描述' }}
          </div>
        </div>

        <!-- 依赖任务 -->
        <div class="field-group">
          <label>🔗 依赖任务</label>
          <div v-if="editing" class="dep-editor">
            <select v-model="form.dependencies" multiple class="dep-select">
              <option v-for="t in availableDeps" :key="t.id" :value="t.id">
                {{ t.title }} ({{ t.status }})
              </option>
            </select>
          </div>
          <div v-else>
            <span v-if="task.dependency_count === 0" class="placeholder" @click="startEdit">无依赖（点击编辑）</span>
            <div v-else>{{ task.dependencies }} 个依赖任务</div>
          </div>
        </div>

        <!-- AI Prompt（ai/hybrid 类型显示）-->
        <div v-if="task.task_type !== 'manual'" class="field-group">
          <label>🤖 AI Prompt</label>
          <textarea v-if="editing" v-model="form.ai_prompt" class="field-textarea" rows="4" />
          <div v-else class="field-content editable" @click="startEdit">
            {{ task.ai_prompt || '点击编辑 AI Prompt' }}
          </div>
        </div>

        <!-- 制品列表 -->
        <div class="field-group">
          <label>📦 制品产出</label>
          <ArtifactEditor
            v-for="art in artifacts" :key="art.id"
            :artifact="art"
            @updated="loadArtifacts"
            @deleted="loadArtifacts"
          />
          <div v-if="artifacts.length === 0" class="placeholder">暂无制品</div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-row">
          <button v-if="canExecuteAI" class="action-btn ai-btn" @click="handleExecute" :disabled="executing">
            {{ executing ? 'AI 执行中...' : '🤖 执行 AI' }}
          </button>
          <button v-if="canApprove" class="action-btn approve-btn" @click="handleApprove">✅ 审核通过</button>
          <button v-if="canStartWork" class="action-btn work-btn" @click="handleStartWork">🔨 开始工作</button>
          <button v-if="canComplete" class="action-btn done-btn" @click="handleComplete">✓ 完成</button>
          <button v-if="!editing" class="action-btn edit-btn" @click="startEdit">✏️ 编辑</button>
          <button v-if="editing" class="action-btn save-btn" @click="handleSave">💾 保存</button>
          <button v-if="editing" class="action-btn" @click="editing = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

Script 核心逻辑：

```typescript
const props = defineProps<{ taskId: number }>();
const emit = defineEmits<{ close: []; refresh: [] }>();
const kanbanStore = useKanbanStore();
const task = computed(() => kanbanStore.currentTask);
const artifacts = ref<Artifact[]>([]);
const editing = ref(false);
const executing = ref(false);

const form = reactive({
  title: "", description: "", ai_prompt: "", dependencies: [] as number[],
});

onMounted(async () => {
  await kanbanStore.fetchTask(props.taskId);
  await loadArtifacts();
});

async function loadArtifacts() {
  await kanbanStore.fetchTaskArtifacts(props.taskId);
  artifacts.value = kanbanStore.artifacts;
}

function startEdit() {
  if (!task.value) return;
  Object.assign(form, {
    title: task.value.title,
    description: task.value.description,
    ai_prompt: task.value.ai_prompt,
    dependencies: task.value.dependencies || [],
  });
  editing.value = true;
}

async function handleSave() {
  await kanbanStore.updateTask(props.taskId, form);
  editing.value = false;
  emit("refresh");
}

async function handleExecute() {
  executing.value = true;
  try { await kanbanStore.executeTask(props.taskId); }
  finally { executing.value = false; }
  await loadArtifacts();
  emit("refresh");
}

async function handleApprove() {
  const nextStatus = task.value?.task_type === "hybrid" ? "in_progress" : "done";
  await kanbanStore.updateTaskStatus(props.taskId, nextStatus);
  emit("refresh");
}

async function handleStartWork() {
  await kanbanStore.updateTaskStatus(props.taskId, "in_progress");
  emit("refresh");
}

async function handleComplete() {
  await kanbanStore.updateTaskStatus(props.taskId, "done");
  emit("refresh");
}

const canExecuteAI = computed(() =>
  task.value?.task_type !== "manual" && task.value?.status === "todo"
);
const canApprove = computed(() => task.value?.status === "review");
const canStartWork = computed(() => task.value?.status === "todo" && task.value?.task_type === "manual");
const canComplete = computed(() => task.value?.status === "in_progress");
```

CSS 参照 `ArticleDetailView.vue` 的 `.detail-panel` + 右侧滑出动画模式，使用与项目一致的 CSS 变量（`--bg-secondary`、`--border-primary`、`--accent` 等）。

- [ ] **步骤 2：编写完整的 ContextManager.vue**

替换占位内容：

```vue
<!-- frontend/src/views/kanban/ContextManager.vue -->
<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>项目上下文</h3>
      <div v-for="ctx in kanbanStore.contexts" :key="ctx.id" class="context-item">
        <div class="ctx-header">
          <span class="ctx-title">{{ ctx.title }}</span>
          <span class="ctx-type">{{ ctx.content_type }}</span>
          <button class="del-btn" @click="kanbanStore.deleteContext(ctx.id)">删除</button>
        </div>
        <div class="ctx-content">{{ ctx.content }}</div>
        <button class="edit-btn" @click="editCtx(ctx)">编辑</button>
      </div>
      <div v-if="kanbanStore.contexts.length === 0" class="empty">暂无上下文卡片</div>
      <div class="add-form">
        <input v-model="newCtx.title" placeholder="卡片标题" class="form-input" />
        <select v-model="newCtx.content_type" class="form-select">
          <option value="core_info">核心信息</option>
          <option value="tech_stack">技术栈</option>
          <option value="architecture">架构决策</option>
          <option value="custom">自定义</option>
        </select>
        <textarea v-model="newCtx.content" placeholder="卡片内容（Markdown）" class="form-textarea" rows="3" />
        <button class="btn-primary" @click="handleAdd" :disabled="!newCtx.title.trim()">添加</button>
      </div>
      <div class="dialog-actions">
        <button class="btn-cancel" @click="$emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue";
import { useKanbanStore } from "@/stores/kanban";

const props = defineProps<{ visible: boolean; projectId: number }>();
defineEmits<{ close: [] }>();
const kanbanStore = useKanbanStore();

const newCtx = reactive({ title: "", content_type: "custom", content: "" });

onMounted(() => { kanbanStore.fetchContexts(props.projectId); });

async function handleAdd() {
  if (!newCtx.title.trim()) return;
  await kanbanStore.createContext(props.projectId, { ...newCtx });
  Object.assign(newCtx, { title: "", content_type: "custom", content: "" });
}

function editCtx(ctx: any) {
  const newContent = prompt("编辑内容:", ctx.content);
  if (newContent !== null) {
    kanbanStore.updateContext(ctx.id, { content: newContent });
  }
}
</script>
```

CSS 复用项目对话框样式（`.dialog-overlay`、`.dialog`、`.btn-primary`、`.btn-cancel`）。

- [ ] **步骤 3：编写 ArtifactEditor.vue**

```vue
<!-- frontend/src/views/kanban/ArtifactEditor.vue -->
<template>
  <div class="artifact-card">
    <div class="artifact-header">
      <span class="artifact-title">{{ artifact.title }}</span>
      <span class="artifact-type">{{ artifact.artifact_type === 'ai_generated' ? '🤖 AI' : '✋ 手动' }}</span>
    </div>
    <div v-if="!editing" class="artifact-content md-render" v-html="renderMd(artifact.content)" />
    <textarea v-else v-model="editContent" class="edit-textarea" rows="8" />
    <div class="artifact-actions">
      <button v-if="!editing" class="action-btn" @click="startEdit">✏️ 编辑</button>
      <button v-if="!editing" class="action-btn" @click="handleExport">📥 下载</button>
      <button v-if="editing" class="action-btn save-btn" @click="handleSave">保存</button>
      <button v-if="editing" class="action-btn" @click="editing = false">取消</button>
      <button class="action-btn del-btn" @click="handleDelete">🗑</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useKanbanStore } from "@/stores/kanban";
import type { Artifact } from "@/stores/kanban";
import { marked } from "marked";

marked.setOptions({ breaks: true, gfm: true });
const props = defineProps<{ artifact: Artifact }>();
const emit = defineEmits<{ updated: []; deleted: [] }>();
const kanbanStore = useKanbanStore();
const editing = ref(false);
const editContent = ref("");

function renderMd(text: string): string {
  return marked.parse(text) as string;
}

function startEdit() {
  editContent.value = props.artifact.content;
  editing.value = true;
}

async function handleSave() {
  await kanbanStore.updateArtifact(props.artifact.id, { content: editContent.value });
  editing.value = false;
  emit("updated");
}

function handleExport() {
  const url = kanbanStore.getArtifactExportUrl(props.artifact.id);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${props.artifact.title.slice(0, 50)}.md`;
  a.click();
}

async function handleDelete() {
  await kanbanStore.deleteArtifact(props.artifact.id);
  emit("deleted");
}
</script>

<style scoped>
.artifact-card {
  background: var(--bg-primary); border: 1px solid var(--border-secondary);
  border-radius: var(--radius-sm); padding: 12px; margin-bottom: 8px;
}
.artifact-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.artifact-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.artifact-type { font-size: 11px; color: var(--text-muted); }
.artifact-content { font-size: 13px; color: var(--text-primary); line-height: 1.6; max-height: 300px; overflow-y: auto; }
.edit-textarea {
  width: 100%; background: var(--bg-primary); border: 1px solid var(--accent);
  border-radius: var(--radius-sm); color: var(--text-primary);
  font-size: 13px; padding: 8px; line-height: 1.6; font-family: inherit; resize: vertical; outline: none;
}
.artifact-actions { display: flex; gap: 6px; margin-top: 8px; }
.action-btn {
  padding: 4px 10px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 11px;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
.save-btn { border-color: #3fb950; color: #3fb950; }
.del-btn:hover { border-color: #f85149; color: #f85149; }
/* Markdown rendered content (reused pattern from ArticleDetailView) */
.md-render { font-size: 13px; line-height: 1.7; color: var(--text-primary); word-break: break-word; }
.md-render :deep(h1), .md-render :deep(h2), .md-render :deep(h3) { margin: 12px 0 6px; font-weight: 600; }
.md-render :deep(p) { margin: 4px 0; }
.md-render :deep(ul), .md-render :deep(ol) { padding-left: 18px; margin: 4px 0; }
.md-render :deep(code) { background: rgba(110,118,129,0.15); padding: 2px 4px; border-radius: 3px; font-size: 12px; }
.md-render :deep(pre) { background: rgba(110,118,129,0.1); padding: 10px; border-radius: var(--radius-sm); overflow-x: auto; }
.md-render :deep(pre code) { background: none; padding: 0; }
</style>
```

- [ ] **步骤 4：验证前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功。

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/views/kanban/
git commit -m "feat(kanban): 完善任务详情面板、上下文管理和制品编辑"
```

---

## 任务 9：设置页

**文件：**
- 重写：`frontend/src/views/kanban/settings/KanbanSettingsView.vue`

- [ ] **步骤 1：编写设置页**

```vue
<!-- frontend/src/views/kanban/settings/KanbanSettingsView.vue -->
<template>
  <div class="kanban-settings">
    <h1>看板设置</h1>

    <div class="section">
      <div class="section-header">
        <h2>AI 配置</h2>
      </div>
      <div class="setting-row">
        <span>AI 模型</span>
        <input
          v-model="config.ai_model"
          class="setting-input"
          placeholder="deepseek-chat"
        />
      </div>
      <div class="setting-column">
        <label class="setting-label">系统 Prompt</label>
        <textarea
          v-model="config.ai_system_prompt"
          class="setting-textarea"
          rows="5"
          placeholder="你是一个项目管理助手..."
        />
      </div>
      <button class="save-btn" @click="handleSave" :disabled="saving">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { useKanbanStore } from "@/stores/kanban";

const kanbanStore = useKanbanStore();
const saving = ref(false);

const config = reactive({
  ai_model: "",
  ai_system_prompt: "",
});

onMounted(async () => {
  await kanbanStore.fetchConfig();
  if (kanbanStore.config) {
    config.ai_model = kanbanStore.config.ai_model;
    config.ai_system_prompt = kanbanStore.config.ai_system_prompt;
  }
});

async function handleSave() {
  saving.value = true;
  try {
    await kanbanStore.updateConfig(config);
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.kanban-settings { max-width: 700px; }
.kanban-settings h1 { font-size: 24px; color: var(--text-primary); margin-bottom: 20px; }
.section {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 16px; margin-bottom: 16px;
}
.section-header { margin-bottom: 16px; }
.section-header h2 { font-size: 16px; color: var(--text-primary); }
.setting-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px solid var(--border-secondary);
  font-size: 14px; color: var(--text-secondary);
}
.setting-input {
  width: 250px; padding: 6px 10px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 13px;
}
.setting-input:focus { border-color: var(--accent); outline: none; }
.setting-column { padding: 12px 0; border-bottom: 1px solid var(--border-secondary); }
.setting-label { display: block; font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; }
.setting-textarea {
  width: 100%; padding: 10px 12px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 13px; font-family: inherit; resize: vertical; line-height: 1.6;
}
.setting-textarea:focus { border-color: var(--accent); outline: none; }
.save-btn {
  margin-top: 16px; padding: 8px 20px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

- [ ] **步骤 2：验证前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功。

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/views/kanban/settings/
git commit -m "feat(kanban): 添加看板设置页（AI 配置）"
```

---

## 任务 10：端到端验证

- [ ] **步骤 1：运行全部后端测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期：全部 PASS（blog + kanban）。

- [ ] **步骤 2：前端构建**

```bash
cd frontend && npm run build
```

预期：构建成功。

- [ ] **步骤 3：启动开发服务器手动验证**

```bash
# 后端
cd backend && python manage.py runserver

# 前端
cd frontend && npm run dev
```

手动验证流程：
1. 侧边栏出现"项目看板"入口
2. 创建项目 → 进入看板视图
3. 添加项目上下文卡片
4. 创建 AI 任务 → 触发 AI 执行（需配置 AI API key）
5. 创建手动任务 → 状态流转
6. 导出制品 → 下载 .md 文件
7. 设置页配置 AI 模型

- [ ] **步骤 4：Final commit**

```bash
git add -A
git commit -m "feat(kanban): 项目看板模块完成"
```
