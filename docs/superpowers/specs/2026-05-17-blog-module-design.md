# 博客引擎模块设计文档

> 日期：2026-05-17
> 模块名：blog
> 状态：设计确认

## 1. 概述

博客引擎是 Musk 平台的第一个接入模块，核心定位是**知识聚合与深度学习工具**——从 RSS 订阅和手动 URL 输入获取文章，通过二级 AI 过滤流程进行价值评估和内容生成，最终以优美的可视化笔记形式呈现。

### 核心决策

| 项目 | 决策 |
|------|------|
| 原文展示 | 混合策略：iframe 优先 + 本地缓存降级 |
| AI 处理 | 同步阻塞流水线，单容器友好 |
| AI 过滤 | 二级：L1 便宜模型打分，L2 旗舰模型深度输出 |
| 评分 | 统一维度（技术深度、时效性等），分档可配置，分类可自定义 |
| 定时任务 | APScheduler 嵌入 Django |
| RSS 上限 | 40 个源 |
| 列表页 | 瀑布流卡片 + 分类筛选栏 |
| 详情页 | 左右分栏 1:2（AI 笔记 \| 原文） |

## 2. 模块结构

```
backend/apps/blog/
├── __init__.py
├── manifest.py              # 模块注册元数据
├── apps.py                  # Django AppConfig
├── models.py                # 6 张数据表
├── views.py                 # API 视图
├── urls.py                  # URL 路由
├── serializers.py           # DRF 序列化器
├── services/
│   ├── __init__.py
│   ├── fetcher.py           # RSS/URL 内容抓取
│   ├── processor.py         # AI 二级处理流水线
│   └── exporter.py          # MD 文件导出
├── scheduler.py             # APScheduler 定时任务
└── migrations/
```

## 3. 数据模型

模块使用独立 SQLite 数据库（`data/blog.db`），所有模型 `app_label = "apps_blog"`。

### 3.1 Category（分类配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(50, unique) | 分类名称，如"技术"、"AI"、"新闻" |
| icon | CharField(10) | 图标 emoji |
| score_thresholds | JSONField | 分档范围，如 `{"low": [1,3], "mid": [4,6], "high": [7,10]}` |
| article_count | IntegerField | 冗余计数（查询优化） |

用户可自定义分类，每个分类可独立配置分数分档。例如新闻分类可将分档设为 `[1,3]` 和 `[4,10]`（去掉中档，新闻不需要深度学习）。

### 3.2 RSSSource（RSS 源）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(200) | 源名称 |
| url | URLField | RSS feed URL |
| category | FK → Category | 所属分类（可空） |
| fetch_interval | IntegerField | 抓取间隔（秒），默认 3600 |
| last_fetched | DateTimeField | 上次抓取时间 |
| is_active | BooleanField | 是否启用 |
| created_at | DateTimeField | 创建时间 |

上限 40 个，超限后禁用添加。

### 3.3 Article（文章）

| 字段 | 类型 | 说明 |
|------|------|------|
| title | CharField(500) | 文章标题 |
| url | URLField(unique) | 原文链接（去重键） |
| source | FK → RSSSource | 所属 RSS 源（可空，手动 URL 时为 null） |
| category | FK → Category | 分类 |
| status | CharField(20) | pending / processing / done / failed / unparsable |
| score | IntegerField | L1 打分 1-10（可空） |
| source_name | CharField(200) | 来源名称 |
| published_at | DateTimeField | 原文发布时间 |
| summary | TextField | AI 生成的总结 |
| key_points | TextField | AI 生成的要点（JSON 数组格式） |
| deep_analysis | TextField | AI 深度分析 |
| raw_html | TextField | 抓取的原始 HTML（缓存） |
| raw_text | TextField | trafilatura 提取的纯文本 |
| created_at | DateTimeField | 入库时间 |
| updated_at | DateTimeField | 最后更新时间 |

### 3.4 FailedURL（无效链接）

| 字段 | 类型 | 说明 |
|------|------|------|
| url | URLField(unique) | 失败的 URL |
| reason | CharField(200) | 失败原因："404"、"timeout"、"paywall" |
| attempted_at | DateTimeField | 尝试时间 |

### 3.5 BlogConfig（抓取配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| key | CharField(50, unique) | 配置键 |
| value | JSONField | 配置值 |

系统配置项：

| key | 默认值 | 说明 |
|-----|--------|------|
| l1_model | deepseek-chat | L1 过滤使用的模型 |
| l2_model | glm-4-plus | L2 深度处理使用的模型 |
| rss_source_limit | 40 | RSS 源上限 |
| default_score_dims | ["技术深度", "时效性", "实用价值", "创新性"] | 默认评分维度 |

### 3.6 ScoreDimension（评分维度）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(50) | 维度名称，如"技术深度"、"时效性" |
| description | TextField | 维度说明 |
| weight | FloatField | 权重（预留，当前统一为 1.0） |

## 4. 数据流

```
RSS 定时抓取 / 手动粘贴 URL
  → fetcher.py: httpx 获取 + trafilatura 提取正文
    ├─ 网络失败(404/5xx/超时) → FailedURL 表
    ├─ 获取到但无法解析 → Article(status='unparsable')，存 raw_html
    └─ 成功提取 → Article(status='pending')
      → processor.py L1: 便宜模型打分 → Article.score
        ├─ 低分(默认 1-3) → 生成 summary → done
        ├─ 中分(默认 4-6) → L2: summary + key_points → done
        └─ 高分(默认 7-10) → L2: summary + key_points + deep_analysis → done
```

## 5. AI 处理流水线

### 5.1 fetcher.py

```python
def fetch_rss(source: RSSSource) -> list[dict]:
    """抓取 RSS feed，解析条目列表"""
    # feedparser 解析 RSS
    # 逐条 URL 去重（Article + FailedURL）
    # 返回待处理条目列表

def fetch_article(url: str) -> dict:
    """抓取单篇文章"""
    # 1. httpx.get(url, timeout=15, follow_redirects=True)
    # 2. 失败 → {"status": "failed", "reason": str}
    # 3. 成功 → trafilatura.extract(html)
    #    - 空 → {"status": "unparsable", "raw_html": html}
    #    - 非空 → {"status": "pending", "raw_text": text, ...}
```

### 5.2 processor.py

```python
def process_article(article: Article):
    """同步处理单篇文章"""
    article.status = 'processing'
    article.save()

    # L1：便宜模型打分
    l1_prompt = build_l1_prompt(score_dimensions)
    adapter_l1 = get_adapter(config.l1_model)
    l1_result = adapter_l1.chat(messages=[
        {"role": "system", "content": l1_prompt},
        {"role": "user", "content": article.raw_text[:3000]},
    ])
    article.score = parse_score(l1_result)

    # 根据分类分档决定处理深度
    thresholds = article.category.score_thresholds

    if article.score <= thresholds["low"][1]:
        # 低分：仅总结
        article.summary = generate_summary(adapter_l1, article.raw_text[:2000])

    elif article.score <= thresholds["mid"][1]:
        # 中分：总结 + 要点
        adapter_l2 = get_adapter(config.l2_model)
        article.summary = generate_summary(adapter_l2, article.raw_text)
        article.key_points = generate_key_points(adapter_l2, article.raw_text)

    else:
        # 高分：全套
        adapter_l2 = get_adapter(config.l2_model)
        article.summary = generate_summary(adapter_l2, article.raw_text)
        article.key_points = generate_key_points(adapter_l2, article.raw_text)
        article.deep_analysis = generate_deep_analysis(adapter_l2, article.raw_text)

    article.status = 'done'
    article.save()
```

### 5.3 scheduler.py

```python
def start_scheduler():
    """Django 启动时调用，注册所有活跃 RSS 源的定时任务"""
    scheduler = BackgroundScheduler()
    for source in RSSSource.objects.filter(is_active=True):
        scheduler.add_job(
            fetch_and_process,
            'interval',
            seconds=source.fetch_interval,
            args=[source.id],
            id=f'rss_{source.id}',
            replace_existing=True,
        )
    scheduler.start()
```

- Django `apps.py` 的 `ready()` 中调用
- RSS 源增删改时动态更新 scheduler job
- `fetch_and_process()` 逐文章同步处理，单篇失败不阻塞后续

### 5.4 exporter.py

```python
def export_article_md(article: Article) -> str:
    """导出单篇为 MD（不含原文）"""
    return f"""# {article.title}

> Source: [{article.source_name}]({article.url}) | Level: {article.score}/10

## Summary
{article.summary}

## Key Points
{format_key_points(article.key_points)}

## DeepAnalysis
{article.deep_analysis or '_未进行深度分析_'}
"""
```

## 6. API 端点

挂载于 `/api/blog/`，需要 JWT 认证。

### 6.1 文章

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/articles/` | GET | 文章列表 | `?category=&score_min=&status=&page=` |
| `/articles/:id/` | GET | 文章详情 | — |
| `/articles/fetch_url/` | POST | 手动 URL 抓取 | `{url, category_id?}` |
| `/articles/:id/reprocess/` | POST | 重新 AI 处理 | — |
| `/articles/:id/` | DELETE | 删除文章 | — |
| `/articles/:id/export/` | POST | 导出单篇 MD | — |
| `/articles/export_batch/` | POST | 批量导出 | `{article_ids, category_id}` |

### 6.2 分类

| 端点 | 方法 | 说明 |
|------|------|------|
| `/categories/` | GET | 分类列表（含文章计数） |
| `/categories/` | POST | 新建分类 |
| `/categories/:id/` | PUT | 更新分类（含分档） |
| `/categories/:id/` | DELETE | 删除分类 |

### 6.3 RSS 源

| 端点 | 方法 | 说明 |
|------|------|------|
| `/rss-sources/` | GET | RSS 源列表 |
| `/rss-sources/` | POST | 添加 RSS 源（上限 40） |
| `/rss-sources/:id/` | PUT | 更新 RSS 源 |
| `/rss-sources/:id/` | DELETE | 删除 RSS 源 |
| `/rss-sources/:id/fetch/` | POST | 手动触发抓取 |

### 6.4 配置

| 端点 | 方法 | 说明 |
|------|------|------|
| `/config/` | GET | 获取博客配置 |
| `/config/` | PUT | 更新配置 |
| `/failed-urls/` | GET | 无效链接列表 |
| `/failed-urls/:id/` | DELETE | 删除无效链接 |

### 6.5 调度

| 端点 | 方法 | 说明 |
|------|------|------|
| `/scheduler/status/` | GET | 调度状态 |
| `/scheduler/fetch_all/` | POST | 全量抓取 |

## 7. 前端组件

### 7.1 组件树

```
src/views/blog/
├── BlogListView.vue             列表页主容器
│   ├── CategoryFilter.vue       顶部分类/分数筛选栏
│   └── ArticleCard.vue          瀑布流卡片
├── ArticleDetailView.vue        详情页主容器
│   ├── NotePanel.vue            左 1/3：AI 笔记
│   └── SourcePanel.vue          右 2/3：原文展示
├── settings/
│   ├── BlogSettingsView.vue     设置页（4 Tab）
│   ├── RSSManager.vue           Tab1: RSS 源管理
│   ├── CategoryManager.vue      Tab2: 分类配置
│   ├── ScoreSettings.vue        Tab3: 评分设置
│   └── SchedulerPanel.vue       Tab4: 调度与工具
└── AddUrlDialog.vue             手动粘贴 URL 弹窗
```

### 7.2 列表页（BlogListView）

- 顶部横向分类筛选栏：全部 / 技术 / AI / 新闻 / ... + ⭐7+ 高价值
- 双列瀑布流卡片，时间倒序，无限滚动
- 卡片内容：分类标签、分数角标、标题、摘要前 80 字、标签
- 低分卡片 opacity: 0.6 降低视觉权重
- 无效文章单独分组或末尾灰色区域
- 右上角 "+" 按钮 → AddUrlDialog

### 7.3 详情页（ArticleDetailView）

- 左 1/3 `NotePanel`：纵向排列 Summary → Key Points → Deep Analysis
- 右 2/3 `SourcePanel`：
  - 优先 iframe 加载原文 URL
  - iframe 失败 → 降级展示缓存的 raw_text（纯净文本排版）
  - unparsable → 提示"无法提取正文"+ 外链按钮
- 顶部操作栏：导出 MD、重新处理、返回列表

### 7.4 设置页（BlogSettingsView）

- **RSSManager**：表格展示源信息，上限 40，超限禁用添加按钮并提示
- **CategoryManager**：分类 CRUD + 内联编辑分档范围（三个输入框）
- **ScoreSettings**：评分维度增删、L1/L2 模型下拉选择
- **SchedulerPanel**：各源下次抓取时间、全量抓取按钮、无效链接列表

### 7.5 前端路由

```typescript
{ path: '/blog', children: [
  { path: '', component: BlogListView },
  { path: ':id', component: ArticleDetailView },
  { path: 'settings', component: BlogSettingsView },
]}
```

Sidebar 自动注册 `/blog` 路由项。

## 8. 依赖

### 后端 Python 包

| 包 | 用途 |
|----|------|
| feedparser | RSS feed 解析 |
| trafilatura | 网页正文提取 |
| httpx | HTTP 请求（支持超时和重定向） |
| apscheduler | 定时任务调度 |

### 现有模块依赖

- `module_layer.framework.FrameworkAPI` — AI 适配器访问
- `module_layer.registry` — 模块注册
- `core.ai.adapters` — get_adapter() 工厂
