# Sprint 4: Docker 部署 + 集成验证 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development 逐任务实现此计划。

**目标：** 实现单容器 Docker 部署（Nginx + Vue 静态文件 + Gunicorn + SQLite），docker-compose 一键启动，全功能可用。

**架构：** 多阶段 Dockerfile。Stage 1 用 Node 构建 Vue 前端，Stage 2 用 Python + Nginx 运行。Nginx 监听 80 端口，`/` 返回前端静态文件，`/api/` 反向代理到 Gunicorn:8000，`/media/` 直接服务文件。

**验证标准：** `docker-compose up` → 浏览器访问 → 注册 → 登录 → 看到完整布局 → AI 对话可用

---

## 文件结构

```
新增：
docker/
├── nginx.conf           # Nginx 配置
└── entrypoint.sh        # 启动脚本（迁移 + collectstatic + 启动）
Dockerfile               # 多阶段构建
docker-compose.yml       # 一键启动

修改：
.gitignore               # 添加 dist/ 已有
```
