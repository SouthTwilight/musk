"""MD 文件导出服务。"""


def export_article_md(article) -> str:
    """导出单篇文章为 Markdown（不含原文）。"""
    md = f"""# {article.title}

> Source: [{article.source_name}]({article.url}) | Level: {article.score or 'N/A'}/10

## Summary
{article.summary or '_无总结_'}

## Key Points
{article.key_points or '_无要点_'}

## DeepAnalysis
{article.deep_analysis or '_未进行深度分析_'}
"""
    return md
