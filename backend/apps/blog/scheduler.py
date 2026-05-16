"""APScheduler 定时任务管理。"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler():
    """启动调度器，注册所有活跃 RSS 源的定时任务。"""
    sched = get_scheduler()

    try:
        from apps.blog.models import RSSSource
        db = _get_db()
        for source in RSSSource.objects.using(db).filter(is_active=True):
            _add_source_job(sched, source)
    except Exception as e:
        logger.warning("Failed to register RSS jobs: %s", e)

    if not sched.running:
        sched.start()
        logger.info("Blog scheduler started")


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


def _add_source_job(sched, source):
    """注册单个 RSS 源的定时抓取任务。"""
    def _job(source_id):
        try:
            from apps.blog.models import RSSSource
            from apps.blog.services.fetcher import fetch_rss_source
            db = _get_db()
            src = RSSSource.objects.using(db).get(pk=source_id)
            count = fetch_rss_source(src)
            if count:
                logger.info("Fetched %d new articles from %s", count, src.name)
        except Exception as e:
            logger.error("Scheduled fetch failed for source %s: %s", source_id, e)

    sched.add_job(
        _job,
        "interval",
        seconds=source.fetch_interval,
        args=[source.id],
        id=f"rss_{source.id}",
        replace_existing=True,
    )


def refresh_jobs():
    """刷新所有定时任务（RSS 源变更后调用）。"""
    sched = get_scheduler()
    for job in sched.get_jobs():
        if job.id.startswith("rss_"):
            sched.remove_job(job.id)
    try:
        from apps.blog.models import RSSSource
        db = _get_db()
        for source in RSSSource.objects.using(db).filter(is_active=True):
            _add_source_job(sched, source)
    except Exception as e:
        logger.warning("Failed to refresh RSS jobs: %s", e)
