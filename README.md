# Musk

模块化 AI 增强看板工具平台。集成金融股票分析、项目管理和个人知识库，提供统一的工作空间。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router |
| 后端 | Python / Django 4.2 + Django REST Framework + SimpleJWT |
| 数据库 | SQLite（框架主库 + 每模块独立数据库） |
| AI | DeepSeek / GLM（OpenAI 兼容协议） |
| 部署 | Docker + Nginx + Gunicorn |

## 功能特性

- **JWT 认证闭环** — 注册、登录、Token 刷新，统一 admin 权限
- **暗夜科技主题** — 深色/浅色一键切换，支持自定义背景图
- **可折叠侧边栏** — 响应式布局，220px / 60px 平滑过渡
- **模块自动扫描** — 放入 `apps/` 目录即可自动注册路由、菜单、数据库
- **AI 中枢** — 多模型代理、会话管理、Prompt 模板、SSE 流式输出
- **独立数据库隔离** — 每个模块使用独立 SQLite 文件
- **Docker 一键部署** — 单容器（Nginx + Gunicorn + SQLite）

## 项目结构

```
musk/
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── shell/            # 布局壳（Sidebar、TopBar、AppLayout）
│       ├── core/             # API 层、模块注册表
│       ├── stores/           # Pinia 状态（auth、app、ai）
│       ├── views/            # 页面组件
│       ├── router/           # 路由配置 + 守卫
│       └── styles/           # CSS Variables 主题系统
├── backend/                  # Django 后端
│   ├── musk/                 # 项目配置
│   ├── core/
│   │   ├── auth/             # 认证服务（注册/登录/JWT）
│   │   ├── ai/               # AI 中枢（适配器/会话/模板/SSE）
│   │   ├── config/           # 用户配置（主题/背景图）
│   │   └── storage/          # 文件上传
│   ├── module_layer/         # 模块应用层
│   │   ├── scanner.py        # 自动扫描 apps/ 目录
│   │   ├── registry.py       # 模块注册表
│   │   └── db_router.py      # 多数据库路由器
│   ├── apps/                 # 业务模块目录
│   │   └── demo/             # 示例模块
│   └── tests/                # 测试（24 tests）
├── docker/
│   ├── Dockerfile            # 多阶段构建
│   ├── nginx.conf            # Nginx 配置
│   └── entrypoint.sh         # 启动脚本
├── docker-compose.yml
├── data/                     # SQLite 数据库文件
├── media/                    # 用户上传文件
└── docs/                     # 设计规格与实施计划
```

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone <repo-url> && cd musk

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 SECRET_KEY 和 AI API Key

# 3. 一键启动
docker-compose up -d

# 4. 访问
# http://localhost:8080
```

### 本地开发

```bash
# 后端
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 前端（新终端）
cd frontend
npm install
npm run dev

# 访问 http://localhost:5173
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Django 密钥 | — |
| `DEBUG` | 调试模式 | `True` |
| `ALLOWED_HOSTS` | 允许的主机 | `localhost,127.0.0.1` |
| `JWT_ACCESS_TTL_MINUTES` | Access Token 有效期（分钟） | `30` |
| `JWT_REFRESH_TTL_DAYS` | Refresh Token 有效期（天） | `7` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | — |
| `GLM_API_KEY` | GLM API Key | — |
| `AI_DEFAULT_MODEL` | 默认 AI 模型 | `deepseek` |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register/` | POST | 用户注册 |
| `/api/auth/login/` | POST | 登录（返回 JWT） |
| `/api/auth/refresh/` | POST | 刷新 Token |
| `/api/auth/me/` | GET | 当前用户信息 |
| `/api/config/` | GET/PATCH | 用户配置（主题、背景图） |
| `/api/storage/` | GET/POST | 文件上传 |
| `/api/ai/conversations/` | GET/POST | AI 会话列表/创建 |
| `/api/ai/chat/` | POST | AI 对话（支持 SSE 流式） |
| `/api/ai/templates/` | GET/POST | Prompt 模板 |
| `/api/modules/` | GET | 已注册模块列表 |

## 模块开发

创建新模块只需在 `backend/apps/` 下新建目录并编写 `manifest.py`：

```python
# backend/apps/my_module/manifest.py
MANIFEST = {
    "name": "my_module",
    "version": "1.0.0",
    "display_name": "我的模块",
    "icon": "📦",
    "description": "模块描述",
    "menu_order": 10,
}
```

框架启动时自动扫描并注册：路由挂载到 `/api/my_module/`，菜单自动出现在侧边栏，数据库自动创建独立 `my_module.db`。

## 测试

```bash
cd backend
source .venv/Scripts/activate
python -m pytest tests/ -v
```

当前测试覆盖：认证（10）、配置（5）、模块层（3）、AI（6），共 24 个测试。

## 开发进度

- [x] **Sprint 1** — 项目脚手架 + JWT 认证闭环
- [x] **Sprint 2** — 框架壳 + 暗夜科技主题 + 背景图
- [x] **Sprint 3** — 模块应用层 + AI 中枢 + 示例模块
- [x] **Sprint 4** — Docker 部署 + 集成验证
- [ ] **Phase 2** — 博客引擎模块
- [ ] **Phase 3** — 项目看板模块
- [ ] **Phase 4** — 看板工具模块（金融股票分析）

## License

MIT
