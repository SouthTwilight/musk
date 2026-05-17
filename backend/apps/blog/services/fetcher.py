"""RSS/URL 内容抓取服务。"""

import logging
import re
import json
from datetime import datetime
from time import mktime
from urllib.parse import urlparse

import httpx
import trafilatura
import feedparser

from apps.blog.models import Article, RSSSource, FailedURL

logger = logging.getLogger(__name__)


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


_LOGIN_INDICATORS = ("login", "signin", "sign-in", "accounts/page", "auth")

_MIN_CONTENT_LENGTH = 200  # 正文最短字符数，低于此视为无效


def fetch_article(url: str) -> dict:
    """抓取单篇文章，返回结果字典。"""
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Fetch failed for %s: %s", url, e)
        return {"status": "failed", "reason": str(e)[:200]}

    # 检测重定向到登录页
    final_url = str(resp.url).lower()
    original_host = urlparse(url).netloc.lower()
    final_host = urlparse(str(resp.url)).netloc.lower()
    if final_host != original_host:
        for indicator in _LOGIN_INDICATORS:
            if indicator in final_url:
                logger.warning("Redirected to login page for %s → %s", url, resp.url)
                return {"status": "failed", "reason": "redirected to login page", "url": url}

    html = resp.text

    try:
        text = trafilatura.extract(html)
    except Exception:
        text = None

    if not text or len(text.strip()) < _MIN_CONTENT_LENGTH:
        return {
            "status": "unparsable",
            "raw_html": html,
            "title": _extract_title(html),
            "url": url,
        }

    title = _extract_title(html)
    try:
        meta_json = trafilatura.extract(html, output_format="json")
        if meta_json:
            meta = json.loads(meta_json)
            title = meta.get("title", title)
    except Exception:
        pass

    return {
        "status": "pending",
        "title": title or url,
        "url": url,
        "raw_html": html,
        "raw_text": text,
        "published_at": None,
        "source_name": _extract_source_name(url),
    }


def fetch_and_store_article(url: str, category_id=None) -> dict:
    """抓取单篇文章并存入数据库。"""
    db = _get_db()

    if Article.objects.using(db).filter(url=url).exists():
        return {"status": "duplicate", "url": url}
    if FailedURL.objects.using(db).filter(url=url).exists():
        return {"status": "duplicate_failed", "url": url}

    # 解析分类（在 fetch 之前，failed 文章也需要）
    from apps.blog.models import Category
    category = None
    if category_id:
        try:
            category = Category.objects.using(db).get(pk=category_id)
        except Category.DoesNotExist:
            pass

    result = fetch_article(url)

    if result["status"] == "failed":
        FailedURL.objects.using(db).create(
            url=url, reason=result.get("reason", "unknown"),
        )
        Article.objects.using(db).create(
            title=result.get("title", url),
            url=url,
            status="failed",
            source_name=_extract_source_name(url),
            category=category,
        )
        return result

    article = Article.objects.using(db).create(
        title=result.get("title", url),
        url=url,
        status=result["status"],
        raw_html=result.get("raw_html", ""),
        raw_text=result.get("raw_text", ""),
        source_name=result.get("source_name", ""),
        published_at=result.get("published_at"),
        category=category,
    )

    if article.status == "pending" and article.raw_text:
        from apps.blog.services.processor import process_article
        process_article(article)

    return {
        "status": article.status,
        "title": article.title,
        "url": article.url,
        "id": article.id,
        "score": article.score,
    }


def fetch_rss_source(source: RSSSource) -> int:
    """抓取单个 RSS 源，返回新增文章数。"""
    db = _get_db()
    new_count = 0

    try:
        feed = feedparser.parse(source.url)
    except Exception as e:
        logger.error("RSS parse failed for %s: %s", source.name, e)
        return 0

    for entry in feed.entries:
        url = entry.get("link")
        if not url:
            continue
        if Article.objects.using(db).filter(url=url).exists():
            continue
        if FailedURL.objects.using(db).filter(url=url).exists():
            continue

        result = fetch_article(url)

        if result["status"] == "failed":
            FailedURL.objects.using(db).create(
                url=url, reason=result.get("reason", "unknown"),
            )
            continue

        article = Article.objects.using(db).create(
            title=result.get("title", entry.get("title", url)),
            url=url,
            source=source,
            category=source.category,
            status=result["status"],
            raw_html=result.get("raw_html", ""),
            raw_text=result.get("raw_text", ""),
            source_name=source.name,
            published_at=_parse_published(entry),
        )

        if article.status == "pending" and article.raw_text:
            from apps.blog.services.processor import process_article
            process_article(article)

        new_count += 1

    source.last_fetched = datetime.now()
    source.save(using=db)
    return new_count


def fetch_all_sources() -> int:
    """抓取所有活跃 RSS 源。"""
    db = _get_db()
    total = 0
    for source in RSSSource.objects.using(db).filter(is_active=True):
        try:
            total += fetch_rss_source(source)
        except Exception as e:
            logger.error("Error fetching source %s: %s", source.name, e)
    return total


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_source_name(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "")


def _parse_published(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime.fromtimestamp(mktime(entry.published_parsed))
    return None
