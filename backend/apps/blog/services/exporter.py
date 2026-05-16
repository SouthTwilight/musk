"""MD 文件导出服务。"""

import json


def export_article_md(article) -> str:
    """导出单篇文章为 Markdown（不含原文）。"""
    points_text = ""
    if article.key_points:
        try:
            points = json.loads(article.key_points)
            if isinstance(points, list):
                points_text = "\n".join(f"- {p}" for p in points)
            else:
                points_text = str(points)
        except (json.JSONDecodeError, TypeError):
            points_text = article.key_points

    md = f"""# {article.title}

> Source: [{article.source_name}]({article.url}) | Level: {article.score or 'N/A'}/10

## Summary
{article.summary or '_无总结_'}

## Key Points
{points_text or '_无要点_'}

## DeepAnalysis
{article.deep_analysis or '_未进行深度分析_'}
"""
    return md
