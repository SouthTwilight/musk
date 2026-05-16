def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


def process_article(article):
    article.status = "done"
    article.save(using=_get_db())
