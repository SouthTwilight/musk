# Musk 看板工具平台 — 项目主题框架设计

> **文档日期**：2026-05-15
> **设计版本**：v1.0
> **状态**：设计已确认，待实施

---

## 一、设计总览

### 1.1 设计目标

构建一个**可扩展、模块化、AI 增强**的看板工具平台。框架提供认证、AI 中枢、主题、布局等基础能力；业务模块（看板工具、项目看板、博客引擎）以插件形式接入，彼此完全解耦。

### 1.2 核心设计原则

1. **模块隔离优先**：模块间不允许直接引用，所有交互通过框架 API
2. **约定优于配置**：模块遵循 manifest 契约即可自动注册，零配置接入
3. **框架最小化**：框架只做不可缩减的基础服务，不侵入模块业务逻辑
4. **美观一致**：统一的暗夜科技视觉风格，框架壳提供一致的主题系统
5. **YAGNI**：不做过度设计，不为未确认的需求预留功能

### 1.3 全局架构图

```text
┌─────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                        │
│        静态文件 (Vue SPA) + 反向代理 (Django API)          │
└───────────────────────┬─────────────────────────────────┘
                        │
    ┌───────────────────┴───────────────────┐
    │                                       │
    ▼                                       ▼
┌───────────────┐              ┌────────────────────────┐
│  Vue 3 SPA    │   REST API   │  Django 4 应用服务器     │
│  (Vite 构建)  │◄──JWT Auth──►│  (Gunicorn)             │
│               │              │                         │
│  ┌─────────┐  │              │  ┌───────────────────┐  │
│  │ 框架壳   │  │              │  │   框架核心          │  │
│  │ · 布局   │  │              │  │   · 认证 (JWT)     │  │
│  │ · 主题   │  │              │  │   · AI 中枢        │  │
│  │ · 导航   │  │              │  │   · 存储管理       │  │
│  │ · 背景图 │  │              │  │   · 配置管理       │  │
│  └────┬────┘  │              │  └────────┬──────────┘  │
│       │       │              │           │              │
│  ┌────┴────┐  │              │  ┌────────┴──────────┐  │
│  │模块组件  │  │              │  │  模块应用层         │  │
│  │ · 看板   │  │              │  │  · 自动扫描器       │  │
│  │ · 项目   │  │              │  │  · 生命周期管理     │  │
│  │ · 博客   │  │              │  │  · DB 路由分发      │  │
│  └─────────┘  │              │  │  · 接口契约校验      │  │
└───────────────┘              │  └────────┬──────────┘  │
                                │           │              │
                                │  ┌────────┴──────────┐  │
                                │  │   模块实现          │  │
                                │  │   apps/kanban/    │  │
                                │  │   apps/project/   │  │
                                │  │   apps/blog/      │  │
                                │  └────────┬──────────┘  │
                                │           │              │
                                │  ┌────────┴──────────┐  │
                                │  │   数据库层          │  │
                                │  │   · musk.db (框架)  │  │
                                │  │   · kanban.db       │  │
                                │  │   · project.db      │  │
                                │  │   · blog.db         │  │
                                │  └───────────────────┘  │
                                └────────────────────────┘
```

---

## 二、前端框架设计

### 2.1 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 核心框架 |
| Vite | 5.x | 构建工具 |
| Vue Router | 4.x | 路由管理（动态注册） |
| Pinia | 2.x | 状态管理（动态 Store） |
| TypeScript | 5.x | 类型约束 |
| SCSS | — | 样式预处理 + CSS Variables 主题 |
| Axios | 1.x | HTTP 请求 |

### 2.2 框架壳（Shell）

框架壳是所有页面的外层容器，提供：

```text
┌──────────────────────────────────────┐
│  顶栏 (TopBar)                        │
│  ☰ Logo | 面包屑导航        🌙 ☀️ 👤 │
├────────┬─────────────────────────────┤
│ 侧边栏  │                             │
│ (可折叠)│      主内容区                │
│        │      <router-view>           │
│ 📊 看板 │                             │
│ 📋 项目 │   模块组件在此渲染            │
│ 📝 博客 │                             │
│ ⚙️ 设置 │                             │
│        │                             │
└────────┴─────────────────────────────┘
```

**核心能力：**

1. **布局管理**：响应式侧边栏（展开 220px / 折叠 60px），内容区自适应
2. **主题切换**：深色/浅色一键切换，CSS Variables 驱动全局样式变更
3. **背景图**：用户可上传自定义背景图，应用于内容区背景（带透明度叠加）
4. **导航注册**：监听框架提供的 `menuRegistry`，模块注册后自动出现在侧边栏
5. **路由分发**：通过 Vue Router 动态路由注入，模块路由自动挂载

### 2.3 主题系统

**CSS Variables 架构：**

```css
:root {
  /* 暗夜科技深色主题（默认） */
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-sidebar: #010409;
  --border: #21262d;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --accent: #58a6ff;
  --accent-secondary: #7c3aed;
  --danger: #f85149;
  --success: #3fb950;
}

[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f6f8fa;
  --bg-sidebar: #f0f0f5;
  --border: #d0d7de;
  --text-primary: #24292f;
  --text-secondary: #57606a;
  --accent: #0969da;
  --accent-secondary: #6f42c1;
}
```

**背景图系统：**
- 用户上传图片存储于 `/media/backgrounds/`
- 内容区通过 `background-image` + 半透明遮罩叠加实现
- 背景图设置持久化到用户配置

### 2.4 模块前端结构

每个模块在前端的目录结构：

```text
src/modules/<module-name>/
├── index.ts          # 模块注册入口（路由、菜单、Store）
├── router.ts         # 模块路由定义
├── stores/           # 模块 Pinia Store
├── views/            # 页面组件
├── components/       # 模块内部组件
└── api.ts            # 模块 API 调用封装
```

模块通过 `index.ts` 暴露注册接口：

```typescript
// 框架定义的接口
interface ModuleRegistration {
  name: string;
  displayName: string;
  icon: string;
  routes: RouteRecordRaw[];
  stores?: Record<string, StoreDefinition>;
  onInstall?: () => void;
  onUninstall?: () => void;
}
```

---

## 三、后端框架设计

### 3.1 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| Django | 4.2 LTS | Web 框架 |
| Django REST Framework | 3.15+ | REST API |
| Simple JWT | 5.x | JWT 认证 |
| SQLite | 3.x | 数据库引擎 |
| Gunicorn | 22.x | WSGI 服务器 |
| openai SDK | 1.x | AI API 调用（DeepSeek 兼容） |

### 3.2 框架核心（Framework Core）

框架核心是不可缩减的基础服务层，位于 `musk/core/`：

| 服务 | 路径 | 职责 |
|------|------|------|
| 认证服务 | `core/auth/` | 用户注册/登录，JWT 签发/验证，Token 刷新 |
| AI 中枢 | `core/ai/` | 多模型代理、会话管理、Prompt 模板、流式响应 |
| 存储管理 | `core/storage/` | 文件上传（背景图等）、静态资源管理 |
| 配置管理 | `core/config/` | 系统配置（AI Key、主题默认值等）、环境变量管理 |
| 模块管理 | `core/module/` | 模块应用层（见第四节） |

### 3.3 认证服务

```text
POST   /api/auth/register/     # 用户注册
POST   /api/auth/login/        # 登录 → 返回 JWT (access + refresh)
POST   /api/auth/refresh/      # 刷新 Token
GET    /api/auth/me/           # 获取当前用户信息
```

- 所有用户注册后自动获得 admin 权限（`is_staff=True, is_superuser=True`）
- 不区分角色，不设权限等级
- JWT access token 有效期 30 分钟，refresh token 有效期 7 天

### 3.4 AI 中枢

```
框架核心 AI 中枢
├── 模型适配层
│   ├── DeepSeekAdapter   (deepseek-chat, deepseek-reasoner)
│   ├── GLMAdapter        (glm-4, glm-4v)
│   └── BaseAdapter       (扩展接口)
├── 会话管理
│   ├── Conversation CRUD
│   ├── Message 历史存储
│   └── 上下文窗口管理
├── Prompt 模板
│   ├── 框架预设模板 (代码审查、需求分析等)
│   ├── 模块自定义模板 (模块通过 manifest 注册)
│   └── 用户自定义模板
└── API 端点
    POST /api/ai/chat/            # 对话 (支持 SSE 流式)
    POST /api/ai/chat/:id/        # 继续会话
    GET  /api/ai/conversations/   # 会话列表
    GET  /api/ai/templates/       # 模板列表
    POST /api/ai/templates/       # 创建模板
```

**模型适配层设计：**

```python
# 扩展接口 — 未来接入新模型只需实现此接口
class BaseAdapter:
    def chat(self, messages: list, stream: bool) -> Iterator[str]: ...
    def models(self) -> list[str]: ...
```

**Prompt 模板结构：**

```text
{
  "id": "code-review",
  "name": "代码审查",
  "prompt": "请审查以下{语言}代码，关注：{关注点}...",
  "variables": ["语言", "关注点"],
  "module": "framework",        # 所属模块
  "category": "development"     # 分类
}
```

### 3.5 存储管理

| 端点 | 用途 |
|------|------|
| `POST /api/storage/upload/` | 上传文件（背景图等） |
| `GET /api/storage/files/` | 文件列表 |
| `DELETE /api/storage/files/:id/` | 删除文件 |

---

## 四、模块应用层设计

### 4.1 概述

模块应用层是框架核心与业务模块之间的中间层，位于 `musk/module_layer/`。负责模块的自动发现、注册、生命周期管理和数据库路由分发。

### 4.2 自动模块扫描器

**工作流程：**

```text
Django 启动
    │
    ▼
扫描 apps/ 目录
    │
    ├── 发现 apps/kanban/
    │     └── 读取 manifest.py
    │         ├── 验证 name/version 必填项
    │         ├── 检查模块依赖（如果声明）
    │         ├── 注册 URL 路由 → /api/kanban/*
    │         ├── 注册数据库路由 → kanban.db
    │         ├── 注册菜单项 → 侧边栏导航
    │         └── 注册 AI 模板 → AI 中枢
    │
    ├── 发现 apps/project/  → 同上
    │
    ├── 发现 apps/blog/     → 同上
    │
    └── 忽略不合规目录（无 manifest.py 或格式错误）
    │
    ▼
模块就绪，应用启动
```

### 4.3 模块接口契约（manifest.py）

每个模块必须在其根目录提供 `manifest.py`：

```python
MANIFEST = {
    # === 必填 ===
    "name": "kanban",                    # 模块唯一标识
    "version": "1.0.0",                 # 语义化版本
    "display_name": "看板工具",           # 菜单显示名称
    "icon": "chart-bar",                # 菜单图标
    "description": "金融股票分析看板",

    # === 可选 ===
    "dependencies": [],                  # 依赖的其他模块名
    "menu_order": 1,                    # 菜单排序（数字越小越靠前）
    "ai_templates": [                   # 模块注册的 AI 模板
        {
            "id": "stock-analysis",
            "name": "股票分析",
            "prompt": "请分析以下股票数据...",
            "variables": ["股票代码", "时间范围"]
        }
    ],
    "permissions": [],                  # 模块需要的权限（当前无区分）
    "settings": {                       # 模块默认配置
        "default_timeframe": "1D"
    }
}
```

### 4.4 模块生命周期钩子

```python
# 模块可选的 hooks.py
def on_install():
    """模块首次注册时调用（如创建表、初始化数据）"""
    pass

def on_uninstall():
    """模块卸载时调用（如清理数据）"""
    pass

def on_upgrade(from_version: str, to_version: str):
    """模块升级时调用"""
    pass
```

### 4.5 数据库隔离

每个模块使用独立 SQLite 文件：

```text
data/
├── musk.db          # 框架主库 (用户表、配置表、AI会话表、模板表)
├── kanban.db        # 看板模块独立数据库
├── project.db       # 项目模块独立数据库
└── blog.db          # 博客模块独立数据库
```

通过 Django 数据库路由自动分发：

```python
# 框架根据请求 URL 前缀自动路由到对应模块数据库
# /api/kanban/* → kanban.db
# /api/project/* → project.db
# /api/blog/*    → blog.db
```

模块开发者无需关心数据库连接细节，Django ORM 操作自动路由到正确数据库。

### 4.6 框架提供给模块的能力

| 能力 | 调用方式 | 说明 |
|------|----------|------|
| AI 对话 | `framework.ai.chat()` | 调用 AI 模型，支持流式 |
| AI 模板 | `framework.ai.get_templates()` | 获取可用模板 |
| 文件存储 | `framework.storage.upload()` | 上传文件到框架存储 |
| 用户信息 | `request.user` | Django 标准认证 |
| 系统配置 | `framework.config.get()` | 读取框架配置 |

模块通过 `from musk.module_layer import framework` 获取框架能力。

---

## 五、Docker 部署设计

### 5.1 容器架构

```text
┌─────────────────────────────────────┐
│  Docker Container (musk:latest)     │
│                                     │
│  ┌───────────────┐                  │
│  │   Nginx :80   │                  │
│  │  /         → Vue 静态文件        │
│  │  /api/*    → Gunicorn :8000     │
│  │  /media/*  → 静态文件目录        │
│  └───────┬───────┘                  │
│          │                          │
│  ┌───────┴───────┐                  │
│  │  Gunicorn     │                  │
│  │  Django :8000 │                  │
│  └───────────────┘                  │
│          │                          │
│  ┌───────┴───────┐                  │
│  │  SQLite 文件   │                  │
│  │  /data/*.db   │                  │
│  └───────────────┘                  │
└─────────────────────────────────────┘
```

### 5.2 Dockerfile 结构

```dockerfile
# 多阶段构建
# Stage 1: 前端构建 (Node)
# Stage 2: 后端运行 (Python + Nginx)
```

### 5.3 docker-compose.yml

```yaml
services:
  musk:
    build: .
    ports:
      - "8080:80"
    volumes:
      - ./data:/app/data          # 数据库持久化
      - ./media:/app/media        # 上传文件持久化
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - GLM_API_KEY=${GLM_API_KEY}
    restart: unless-stopped
```

---

## 六、项目目录结构

```text
musk/
├── docker/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── entrypoint.sh
├── docker-compose.yml
│
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── shell/               # 框架壳
│   │   │   ├── layouts/         # 布局组件
│   │   │   ├── theme/           # 主题系统
│   │   │   └── components/      # 壳组件 (顶栏、侧边栏)
│   │   ├── core/                # 框架前端核心
│   │   │   ├── api.ts           # Axios 实例 + 拦截器
│   │   │   ├── auth.ts          # 认证 Store + 路由守卫
│   │   │   └── module.ts        # 模块注册表 (前端)
│   │   ├── modules/             # 业务模块目录
│   │   │   ├── kanban/
│   │   │   ├── project/
│   │   │   └── blog/
│   │   ├── App.vue
│   │   └── main.ts
│   └── vite.config.ts
│
├── backend/                     # Django 后端
│   ├── musk/                    # 项目配置
│   │   ├── settings.py
│   │   └── urls.py
│   ├── core/                    # 框架核心
│   │   ├── auth/                # 认证服务
│   │   ├── ai/                  # AI 中枢
│   │   │   ├── adapters/        # 模型适配器
│   │   │   ├── conversations/   # 会话管理
│   │   │   └── templates/       # Prompt 模板
│   │   ├── storage/             # 存储管理
│   │   └── config/              # 配置管理
│   ├── module_layer/            # 模块应用层
│   │   ├── scanner.py           # 自动扫描器
│   │   ├── registry.py          # 模块注册表
│   │   ├── lifecycle.py         # 生命周期管理
│   │   ├── router.py            # DB 路由器
│   │   └── framework.py         # 框架能力暴露给模块
│   ├── apps/                    # 业务模块
│   │   ├── kanban/
│   │   │   ├── manifest.py
│   │   │   ├── urls.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   └── hooks.py
│   │   ├── project/
│   │   └── blog/
│   └── manage.py
│
├── data/                        # 数据库文件 (gitignore)
│   ├── musk.db
│   ├── kanban.db
│   ├── project.db
│   └── blog.db
│
├── media/                       # 上传文件 (gitignore)
│   └── backgrounds/
│
├── docs/                        # 文档
│   └── superpowers/
│       └── specs/
│
├── .env.example                 # 环境变量模板
├── .gitignore
└── CLAUDE.md
```

---

## 七、安全设计

| 层面 | 措施 |
|------|------|
| 传输安全 | JWT + HTTPS（Nginx 配置 SSL） |
| API 安全 | DRF 认证类 + 限流（throttle） |
| 密钥管理 | 环境变量注入，不写入代码或仓库 |
| 前端安全 | Vue 默认 XSS 防护，CSP 头配置 |
| 数据库 | SQLite 文件权限控制，Docker volume 隔离 |
| AI Key | 仅后端持有，前端不可见；存储在配置表中（可加密） |

---

## 八、设计总结

本框架设计的核心创新在于 **模块应用层 + 自动扫描器**：通过 manifest 契约实现模块的零配置自动注册，通过独立数据库文件实现真正的模块数据隔离。框架核心保持最小化，所有业务能力由模块自包含，后期添加/删除模块只需操作对应目录，框架自动感知。

---

> **下一份文档**：项目实施计划（`2026-05-15-musk-implementation-plan.md`）
