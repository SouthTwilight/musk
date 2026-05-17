"""AI 二级处理流水线。"""

import json
import logging
import re

from apps.blog.models import Article, BlogConfig, ScoreDimension

logger = logging.getLogger(__name__)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


def _call_ai(messages: list, model_name: str = None) -> str:
    """调用 AI 模型，返回文本响应。"""
    from core.ai.adapters import get_adapter
    adapter = get_adapter(model_name)
    return adapter.chat(messages, stream=False)


def _get_config(key: str, default=None):
    db = _get_db()
    cfg = BlogConfig.objects.using(db).filter(key=key).first()
    return cfg.value if cfg else default


def _get_default_thresholds() -> dict:
    return {"low": [1, 3], "mid": [4, 6], "high": [7, 10]}


def _get_score_dimensions() -> list[str]:
    db = _get_db()
    dims = list(ScoreDimension.objects.using(db).values_list("name", flat=True))
    if not dims:
        dims = _get_config("default_score_dims", ["技术深度", "时效性", "实用价值", "创新性"])
    return dims


def process_article(article: Article):
    """处理单篇文章的 AI 流水线。"""
    db = _get_db()
    article.status = "processing"
    article.save(using=db)

    try:
        thresholds = (
            article.category.score_thresholds
            if article.category
            else _get_default_thresholds()
        )

        # L1: 便宜模型打分
        l1_model = _get_config("l1_model", "deepseek")
        dims = _get_score_dimensions()
        dims_text = "、".join(dims)

        l1_prompt = f"请对以下文章内容进行评分（1-10分），考虑以下维度：{dims_text}。\n仅返回 JSON 格式：{{\"score\": N, \"tags\": [\"标签1\", \"标签2\"]}}"

        l1_response = _call_ai(
            [
                {"role": "system", "content": l1_prompt},
                {"role": "user", "content": article.raw_text[:3000]},
            ],
            model_name=l1_model,
        )

        score_data = _parse_json(l1_response)
        article.score = score_data.get("score", 5)

        # 根据分档决定处理深度
        if article.score <= thresholds["low"][1]:
            article.summary = _generate_summary(article.raw_text[:2000], l1_model)
        elif article.score <= thresholds["mid"][1]:
            l2_model = _get_config("l2_model", "glm")
            article.summary = _generate_summary(article.raw_text, l2_model)
            article.key_points = _generate_key_points(article.raw_text, l2_model)
        else:
            l2_model = _get_config("l2_model", "glm")
            article.summary = _generate_summary(article.raw_text, l2_model)
            article.key_points = _generate_key_points(article.raw_text, l2_model)
            article.deep_analysis = _generate_deep_analysis(article.raw_text, l2_model)

        article.status = "done"

    except Exception as e:
        logger.error("AI processing failed for article %s: %s", article.id, e)
        article.status = "done"
        article.summary = f"AI 处理失败: {str(e)[:100]}"

    article.save(using=db)


def _generate_summary(text: str, model: str) -> str:
    return _call_ai(
        [
            {"role": "system", "content": "请用中文总结以下文章内容，200字以内。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )


def _generate_key_points(text: str, model: str) -> str:
    return _call_ai(
        [
            {"role": "system", "content": "请提取以下文章的关键要点，以编号列表格式返回（每条一行，格式如：1. xxx），每项不超过30字。不要使用 JSON 格式，不要使用代码块包裹。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )


def _generate_deep_analysis(text: str, model: str) -> str:
    return _call_ai(
        [
            {"role": "system", "content": "请对以下文章进行深度分析，包括：核心观点、技术细节、潜在影响、实践建议。500字以内。"},
            {"role": "user", "content": text},
        ],
        model_name=model,
    )


def _parse_json(text: str) -> dict:
    """从 AI 响应中解析 JSON。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[^}]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"score": 5}
