from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
import io

from apps.blog.models import (
    Category, RSSSource, Article, FailedURL, BlogConfig, ScoreDimension,
)
from apps.blog.serializers import (
    CategorySerializer, RSSSourceSerializer,
    ArticleListSerializer, ArticleDetailSerializer,
    FailedURLSerializer, BlogConfigSerializer, ScoreDimensionSerializer,
    FetchURLSerializer,
)
from apps.blog.services.exporter import export_article_md


def _get_db():
    from module_layer.registry import registry
    info = registry.get("blog")
    return info.db_alias if info else "default"


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=_get_db())


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


class RSSSourceListCreateView(generics.ListCreateAPIView):
    serializer_class = RSSSourceSerializer

    def get_queryset(self):
        return RSSSource.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        # 检查上限
        current_count = RSSSource.objects.using(_get_db()).count()
        limit_cfg = BlogConfig.objects.using(_get_db()).filter(key="rss_source_limit").first()
        limit = limit_cfg.value if limit_cfg else 40
        if current_count >= limit:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"RSS 源已达上限 {limit} 个")
        serializer.save(using=_get_db())


class RSSSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RSSSourceSerializer

    def get_queryset(self):
        return RSSSource.objects.using(_get_db()).all()

    def perform_update(self, serializer):
        serializer.save(using=_get_db())


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer

    def get_queryset(self):
        qs = Article.objects.using(_get_db()).all()
        category = self.request.query_params.get("category")
        status_filter = self.request.query_params.get("status")
        score_min = self.request.query_params.get("score_min")
        if category:
            qs = qs.filter(category_id=category)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if score_min:
            qs = qs.filter(score__gte=int(score_min))
        return qs


class ArticleDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ArticleDetailSerializer

    def get_queryset(self):
        return Article.objects.using(_get_db()).all()


class FetchURLView(APIView):
    """手动粘贴 URL 抓取文章。"""

    def post(self, request):
        serializer = FetchURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]
        category_id = serializer.validated_data.get("category_id")

        from apps.blog.services.fetcher import fetch_and_store_article
        result = fetch_and_store_article(url, category_id=category_id)
        return Response(result, status=status.HTTP_201_CREATED)


class ArticleExportView(APIView):
    """导出单篇文章为 MD。"""

    def post(self, request, pk):
        article = Article.objects.using(_get_db()).get(pk=pk)
        md_content = export_article_md(article)
        buf = io.BytesIO(md_content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f"{article.title[:50]}.md",
            content_type="text/markdown",
        )


class ArticleReprocessView(APIView):
    """重新 AI 处理文章。"""

    def post(self, request, pk):
        article = Article.objects.using(_get_db()).get(pk=pk)
        from apps.blog.services.processor import process_article
        process_article(article)
        return Response({"status": "done"})


class FailedURLListView(generics.ListAPIView):
    serializer_class = FailedURLSerializer

    def get_queryset(self):
        return FailedURL.objects.using(_get_db()).all()


class FailedURLDetailView(generics.DestroyAPIView):
    serializer_class = FailedURLSerializer

    def get_queryset(self):
        return FailedURL.objects.using(_get_db()).all()


class BlogConfigView(APIView):
    """获取/更新博客配置。"""

    def get(self, request):
        configs = BlogConfig.objects.using(_get_db()).all()
        data = {c.key: c.value for c in configs}
        # 补充默认值
        defaults = {
            "l1_model": "deepseek-chat",
            "l2_model": "glm-4-plus",
            "rss_source_limit": 40,
            "default_score_dims": ["技术深度", "时效性", "实用价值", "创新性"],
        }
        for k, v in defaults.items():
            data.setdefault(k, v)
        return Response(data)

    def put(self, request):
        for key, value in request.data.items():
            BlogConfig.objects.using(_get_db()).update_or_create(
                key=key, defaults={"value": value}
            )
        return Response({"detail": "配置已更新"})


class SchedulerStatusView(APIView):
    """调度状态。"""

    def get(self, request):
        sources = RSSSource.objects.using(_get_db()).filter(is_active=True)
        jobs = []
        for s in sources:
            jobs.append({
                "source_id": s.id,
                "name": s.name,
                "interval": s.fetch_interval,
                "last_fetched": s.last_fetched,
            })
        return Response({"jobs": jobs})


class FetchAllView(APIView):
    """手动触发全量抓取。"""

    def post(self, request):
        from apps.blog.services.fetcher import fetch_all_sources
        count = fetch_all_sources()
        return Response({"detail": f"已处理 {count} 篇新文章"})


class ScoreDimensionListCreateView(generics.ListCreateAPIView):
    serializer_class = ScoreDimensionSerializer

    def get_queryset(self):
        return ScoreDimension.objects.using(_get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=_get_db())


class ScoreDimensionDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ScoreDimensionSerializer

    def get_queryset(self):
        return ScoreDimension.objects.using(_get_db()).all()


class BatchExportView(APIView):
    """批量导出。"""

    def post(self, request):
        article_ids = request.data.get("article_ids", [])
        category_id = request.data.get("category_id")

        qs = Article.objects.using(_get_db()).all()
        if article_ids:
            qs = qs.filter(id__in=article_ids)
        elif category_id:
            qs = qs.filter(category_id=category_id)

        parts = []
        for article in qs:
            parts.append(export_article_md(article))
            parts.append("\n\n---\n\n")

        content = "".join(parts)
        buf = io.BytesIO(content.encode("utf-8"))
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename="articles_export.md",
            content_type="text/markdown",
        )
