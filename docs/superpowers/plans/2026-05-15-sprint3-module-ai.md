# Sprint 3: 模块应用层 + AI 中枢 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development 逐任务实现此计划。

**目标：** 实现模块自动扫描与注册系统、AI 中枢（多模型代理 + 会话管理 + Prompt 模板 + SSE 流式）、示例 demo 模块验证全链路。

**架构：** 后端 module_layer/ 负责扫描 apps/ 目录下的模块 manifest 并自动注册路由/DB/菜单。core/ai/ 提供统一 AI 调用接口，支持 DeepSeek 和 GLM。前端通过 /api/modules/ 获取已注册模块列表动态生成侧边栏菜单。

**验证标准：** demo 模块自动出现在导航和路由中；AI 对话可正常调用并流式输出；会话可保存和恢复。

---

## 后端新增文件

```
backend/
├── module_layer/
│   ├── __init__.py
│   ├── scanner.py          # 自动扫描 apps/ 目录
│   ├── registry.py          # 模块注册表（内存）
│   ├── db_router.py         # 多数据库路由器
│   ├── framework.py         # 框架能力暴露
│   └── views.py             # /api/modules/ 端点
├── core/
│   └── ai/
│       ├── __init__.py
│       ├── apps.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py      # BaseAdapter 接口
│       │   └── openai_compat.py  # DeepSeek/GLM (OpenAI 兼容)
│       ├── models.py        # Conversation + Message + PromptTemplate
│       ├── serializers.py
│       ├── views.py         # CRUD + SSE 流式
│       └── urls.py
├── apps/
│   └── demo/
│       ├── __init__.py
│       ├── manifest.py      # 模块元数据
│       ├── models.py
│       ├── views.py
│       └── urls.py
└── tests/
    ├── test_module_layer.py
    └── test_ai.py
```

## 前端新增/修改文件

```
frontend/src/
├── core/
│   └── module.ts            # 模块注册表（前端）
├── stores/
│   └── ai.ts                # AI Store（会话、模板）
├── views/
│   └── AiChatView.vue       # AI 对话页面
└── shell/
    └── Sidebar.vue          # 修改：动态菜单
```
