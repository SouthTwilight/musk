"""请求日志中间件 — 记录每个 HTTP 请求的方法、路径、状态码和耗时。"""

import logging
import time

logger = logging.getLogger("musk.request")


class RequestLoggingMiddleware:
    """记录所有 API 请求的日志。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = (time.monotonic() - start) * 1000
        method = request.method
        path = request.get_full_path()
        status = response.status_code

        # 静态文件和 favicon 不记录
        if path.startswith("/static/") or path == "/favicon.ico":
            return response

        level = logging.INFO
        if status >= 500:
            level = logging.ERROR
        elif status >= 400:
            level = logging.WARNING

        logger.log(
            level,
            "%s %s → %s (%.0fms)",
            method,
            path,
            status,
            duration_ms,
        )

        return response
