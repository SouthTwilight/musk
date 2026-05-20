# 项目看板模块设计规格

> 日期: 2026-05-20
> 模块名: kanban
> 状态: 待实现

## 概述

AI 深度集成的项目看板模块，作为 Musk 平台的新模块应用。支持单人项目管理，提供经典看板视图，AI 可执行设计/规划类任务并产出文本制品，任务间通过前置依赖和制品引用形成知识链条。

### 核心定位

- 单人项目管理工具
- AI 可实际执行任务（产出文本制品），不仅是辅助建议
- 任务双轨制：AI 任务需审核，人工任务直接推进
- 与博客模块同级，遵循 Musk 模块框架规范

### 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 用户模式 | 单人 | 无需权限/角色模型，降低复杂度 |
| AI 产出形式 | 纯文本（Markdown/表格/结构化文本） | 不涉及多模态，与现有 AI 适配器一致 |
| 任务执行模型 | AI 产出需审核确认 | AI 不自动执行动作，所有结果经人工确认 |
| 项目上下文 | 手动维护 + 制品自动关联 | 核心信息人工管理，任务制品自动汇入知识库 |
| 依赖模型 | 前置依赖 + 制品引用 | 双层依赖：顺序控制和上下文传递 |
| 主视图 | 经典看板，卡片可点击展开详情 | 直观展示项目全貌，详情面板聚焦单个任务 |
| AI 配置 | 模块独立配置 | 框架提供 AI 能力，各模块自行管理模型/prompt |
| 方案范围 | 最小可行（MVP） | 与博客模块体量一致，后续可迭代 |

---

## 数据模型

数据库: `data/kanban.db`（独立 SQLite）

### Project（项目）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| name | VARCHAR(100) | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| status | VARCHAR(20) | NOT NULL, default='active' | `active` / `archived` |
| created_at | DATETIME | auto_now_add | 创建时间 |
| updated_at | DATETIME | auto_now | 更新时间 |

### ProjectContext（项目知识卡片）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| project | FK → Project | NOT NULL, on_delete=CASCADE | 所属项目 |
| content_type | VARCHAR(30) | NOT NULL | `core_info` / `tech_stack` / `architecture` / `custom` |
| title | VARCHAR(100) | NOT NULL | 卡片标题 |
| content | TEXT | | 卡片内容（Markdown） |
| updated_at | DATETIME | auto_now | 更新时间 |

每个项目可有多个上下文卡片。AI 执行任务时自动带上该项目的所有上下文卡片内容作为 prompt 的一部分。

### Task（任务）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| project | FK → Project | NOT NULL, on_delete=CASCADE | 所属项目 |
| title | VARCHAR(200) | NOT NULL | 任务标题 |
| description | TEXT | | 任务描述 |
| task_type | VARCHAR(20) | NOT NULL, default='manual' | `manual` / `ai` / `hybrid` |
| status | VARCHAR(20) | NOT NULL, default='todo' | 见状态机 |
| priority | VARCHAR(10) | NOT NULL, default='medium' | `low` / `medium` / `high` |
| ai_prompt | TEXT | | AI 执行时的 prompt（ai/hybrid 类型） |
| parent_task | FK → Task | null, on_delete=SET_NULL | 父任务（子任务支持） |
| position | Integer | default=0 | 看板列内排序 |
| created_at | DATETIME | auto_now_add | 创建时间 |
| updated_at | DATETIME | auto_now | 更新时间 |

**多对多关系：**
- `dependencies` M2M → Task（self, symmetrical=false）：前置依赖任务
- `input_artifacts` M2M → Artifact：引用的上游制品

**状态机：**

```
manual 任务:
  todo → in_progress → done

ai 任务:
  todo → ai_running → review → done

hybrid 任务:
  todo → ai_running → review → in_progress → done

通用:
  任何状态 → cancelled
```

- `todo`: 待办
- `ai_running`: AI 执行中
- `review`: 待审核（AI 制品已生成，等待人工确认）
- `in_progress`: 人工进行中
- `done`: 已完成
- `cancelled`: 已取消

### Artifact（制品）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| task | FK → Task | NOT NULL, on_delete=CASCADE | 产出该制品的任务 |
| project | FK → Project | NOT NULL, on_delete=CASCADE | 所属项目 |
| title | VARCHAR(200) | NOT NULL | 制品标题 |
| content | TEXT | | 制品内容（Markdown） |
| artifact_type | VARCHAR(30) | NOT NULL, default='ai_generated' | `ai_generated` / `manual` |
| created_at | DATETIME | auto_now_add | 创建时间 |

### KanbanConfig（模块配置）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, auto | 主键 |
| ai_model | VARCHAR(100) | default='deepseek-chat' | AI 执行任务使用的模型 |
| ai_system_prompt | TEXT | | AI 系统级 prompt 指令 |

单行配置表（与博客模块 BlogConfig 模式一致），模块初始化时自动创建默认实例。

---

## API 设计

路由前缀: `/api/kanban/`

### 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/projects/` | 项目列表 |
| POST | `/projects/` | 创建项目 |
| GET | `/projects/{id}/` | 项目详情（含上下文卡片、统计信息） |
| PATCH | `/projects/{id}/` | 更新项目 |
| DELETE | `/projects/{id}/` | 删除项目（级联删除） |

### 项目上下文

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/projects/{id}/contexts/` | 获取项目的所有上下文卡片 |
| POST | `/projects/{id}/contexts/` | 添加上下文卡片 |
| PATCH | `/contexts/{id}/` | 更新上下文卡片 |
| DELETE | `/contexts/{id}/` | 删除上下文卡片 |

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/projects/{id}/tasks/` | 项目下所有任务（支持 `?status=` 筛选） |
| POST | `/projects/{id}/tasks/` | 创建任务 |
| GET | `/tasks/{id}/` | 任务详情（含依赖列表、制品列表） |
| PATCH | `/tasks/{id}/` | 更新任务 |
| DELETE | `/tasks/{id}/` | 删除任务 |
| POST | `/tasks/{id}/execute/` | 触发 AI 执行（仅 ai/hybrid 类型） |
| PATCH | `/tasks/{id}/status/` | 快捷状态变更（看板拖拽用） |

### 制品管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tasks/{id}/artifacts/` | 任务的所有制品 |
| POST | `/tasks/{id}/artifacts/` | 手动添加制品 |
| GET | `/projects/{id}/artifacts/` | 项目级制品列表（全部任务） |
| PATCH | `/artifacts/{id}/` | 更新制品 |
| DELETE | `/artifacts/{id}/` | 删除制品 |
| GET | `/artifacts/{id}/export/` | 导出单个制品（下载 .md 文件） |
| GET | `/projects/{id}/artifacts/export/` | 导出项目全部制品（打包下载 .md 文件） |

### 模块配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/config/` | 获取配置 |
| PATCH | `/config/` | 更新配置 |

共 5 组，18 个端点。

---

## AI 集成

### 执行流程

用户触发 AI 执行（点击"执行 AI"按钮）时：

```
1. 前置检查
   ├── 验证任务类型为 ai 或 hybrid
   ├── 验证状态为 todo
   └── 验证所有前置依赖任务状态为 done

2. 状态变更: todo → ai_running

3. 组装 Prompt
   ├── 系统指令（KanbanConfig.ai_system_prompt）
   ├── 项目上下文（该项目所有 ProjectContext 卡片）
   ├── 上游制品（该任务 input_artifacts 引用的制品内容）
   ├── 依赖任务摘要（前置依赖任务的标题 + 最新制品摘要）
   └── 任务自身 ai_prompt 字段

4. 调用 AI
   └── 通过 core.ai 适配器，使用 KanbanConfig.ai_model 模型
   └── 同步阻塞调用（与博客模块一致）

5. 写入制品
   └── AI 返回内容存为 Artifact（artifact_type=ai_generated）
   └── 任务状态变更: ai_running → review

6. 用户审核
   ├── 查看制品内容，可编辑/删除
   ├── 重新执行 AI（回到步骤 2）
   └── 确认: review → done（ai 任务）或 review → in_progress（hybrid 任务）
```

### Prompt 组装模板

```
[系统指令]
{KanbanConfig.ai_system_prompt}

[项目上下文]
{遍历 ProjectContext，格式: ## {title}\n{content}}

[上游制品引用]
{遍历 input_artifacts，格式: ### {artifact.title}（来自任务: {task.title}）\n{artifact.content}}

[依赖任务摘要]
{遍历 dependencies，格式: - {task.title}（已完成，{最新制品标题}: {摘要前200字}）}

[任务要求]
{task.ai_prompt}
```

### 默认配置

```python
ai_model: "deepseek-chat"
ai_system_prompt: "你是一个项目管理助手。请根据提供的项目上下文和任务要求，产出结构化的文本制品。输出使用 Markdown 格式。"
```

### 制品导出

**单个制品导出** (`GET /artifacts/{id}/export/`)：
- 返回 `.md` 文件下载响应（Content-Disposition: attachment）
- 文件名格式：`{任务标题}-{制品标题}.md`

**项目全量导出** (`GET /projects/{id}/artifacts/export/`)：
- 将项目所有制品按任务分组，拼接为一个 `.md` 文件下载
- 文件结构：

```markdown
# {项目名称} — 全部制品

## 任务: {任务标题1}

### 制品: {制品标题1.1}
{制品内容}

### 制品: {制品标题1.2}
{制品内容}

## 任务: {任务标题2}
...
```

- 文件名格式：`{项目名称}-全部制品.md`

前端在任务详情面板和项目看板工具栏中提供导出按钮。

### 错误处理

- AI 调用失败：任务状态回退为 `todo`，返回错误信息
- 前置依赖未完成：拒绝执行，返回提示
- AI 超时：同失败处理

---

## 前端设计

### 路由结构

```
/kanban                           → 项目列表页（入口）
/kanban/:projectId                → 看板视图（核心页面）
/kanban/:projectId/task/:taskId   → 任务详情面板（看板叠加层）
/kanban/settings                  → 模块设置（AI 配置）
```

### 页面一：项目列表 (`/kanban`)

- 顶部标题"项目看板"+ 设置按钮 + 新建项目按钮
- 卡片网格展示各项目，每张卡片包含：
  - 项目名称 + 描述
  - 任务统计（总数/完成/AI执行中）
  - 进度条
- 点击项目卡片进入看板视图

### 页面二：看板视图 (`/kanban/:projectId`)

核心页面，经典看板布局：

**5 列泳道：**
1. 待办（todo）— 灰色
2. AI 执行中（ai_running）— 蓝色
3. 待审核（review）— 黄色
4. 进行中（in_progress）— 紫色
5. 已完成（done）— 绿色，内容半透明

**任务卡片信息：**
- 标题
- 类型标签：🤖 AI / ✋ 手动 / 🔀 混合
- 优先级标签：高（红）/ 中（黄）/ 低（灰）
- 依赖状态：🔒 依赖未满足 / ✅ 依赖已完成
- 制品提示：📎 引用制品数量

**交互：**
- 点击卡片：右侧滑出任务详情面板
- 状态变更：通过详情面板操作按钮（MVP 不做拖拽）

### 页面三：任务详情面板

从右侧滑出的叠加层，不离开看板页面。包含：

- 任务类型 + 状态标签
- 标题（可编辑）
- 描述（可编辑）
- 优先级
- 依赖任务列表（可添加/移除）
- 引用制品列表（可添加/移除，从项目已有制品中选择）
- AI Prompt（ai/hybrid 类型显示，可编辑）
- 制品产出列表（AI 生成或手动添加）
- 操作按钮：执行 AI / 编辑 / 删除 / 状态流转

### 页面四：设置页 (`/kanban/settings`)

- AI 模型选择
- 系统 Prompt 编辑（textarea）

### Store 结构

Pinia store (`stores/kanban.ts`)：
- projects / currentProject / tasks / currentTask / artifacts / contexts / config
- CRUD action 方法
- AI 执行 action

### 组件拆分

```
views/kanban/
├── ProjectListView.vue        # 项目列表
├── KanbanBoardView.vue        # 看板主视图
├── TaskDetailPanel.vue        # 任务详情面板
├── TaskCard.vue               # 看板卡片
├── CreateTaskDialog.vue       # 创建任务弹窗
├── ContextManager.vue         # 上下文卡片管理
├── ArtifactEditor.vue         # 制品编辑/查看
└── settings/
    └── KanbanSettingsView.vue # 设置页
```

---

## 后端模块结构

```
backend/apps/kanban/
├── manifest.py           # 模块注册
├── apps.py               # AppConfig
├── models.py             # 数据模型
├── serializers.py        # DRF 序列化器
├── views.py              # API 视图
├── urls.py               # 路由
├── services/
│   ├── __init__.py
│   └── ai_executor.py    # AI 执行逻辑（prompt 组装 + 调用）
└── migrations/
    └── 0001_initial.py
```

### 关键实现细节

**manifest.py:**
```python
MANIFEST = {
    "name": "kanban",
    "version": "1.0.0",
    "display_name": "项目看板",
    "icon": "📋",
    "description": "AI 集成的项目看板管理工具",
}
```

**多数据库路由：** 遵循框架规范，`app_label = "apps_kanban"`，数据库别名 `module_kanban`。所有查询使用 `objects.using(db)` 模式。

**AI 调用：** 通过 `core.ai` 适配器调用，不直接依赖 OpenAI SDK。复用博客模块的 `_call_ai()` 模式。

---

## 非功能需求

- **性能：** AI 调用同步阻塞，前端展示 loading 状态，超时设为 60 秒
- **数据隔离：** 独立 SQLite 数据库，与博客模块完全隔离
- **错误处理：** AI 失败不丢失数据，任务状态安全回退
- **可扩展性：** 数据模型预留子任务（parent_task），MVP 不实现嵌套展示

---

## MVP 范围外

以下功能留待后续迭代：
- 拖拽排序
- 依赖图可视化
- 甘特图/时间线
- 任务模板
- 项目仪表盘统计
- Prompt 模板管理
- 制品版本控制
