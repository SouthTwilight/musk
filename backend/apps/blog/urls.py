from django.urls import path
from apps.blog.views import (
    CategoryListCreateView, CategoryDetailView,
    RSSSourceListCreateView, RSSSourceDetailView,
    ArticleListView, ArticleDetailView,
    FetchURLView, ArticleExportView, ArticleReprocessView,
    FailedURLListView, FailedURLDetailView,
    BlogConfigView, SchedulerStatusView, FetchAllView,
    ScoreDimensionListCreateView, ScoreDimensionDetailView,
    BatchExportView,
)

urlpatterns = [
    # 分类
    path("categories/", CategoryListCreateView.as_view(), name="blog-categories"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="blog-category-detail"),
    # RSS 源
    path("rss-sources/", RSSSourceListCreateView.as_view(), name="blog-rss-sources"),
    path("rss-sources/<int:pk>/", RSSSourceDetailView.as_view(), name="blog-rss-source-detail"),
    # 文章
    path("articles/", ArticleListView.as_view(), name="blog-articles"),
    path("articles/fetch_url/", FetchURLView.as_view(), name="blog-fetch-url"),
    path("articles/export_batch/", BatchExportView.as_view(), name="blog-export-batch"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="blog-article-detail"),
    path("articles/<int:pk>/export/", ArticleExportView.as_view(), name="blog-article-export"),
    path("articles/<int:pk>/reprocess/", ArticleReprocessView.as_view(), name="blog-article-reprocess"),
    # 无效链接
    path("failed-urls/", FailedURLListView.as_view(), name="blog-failed-urls"),
    path("failed-urls/<int:pk>/", FailedURLDetailView.as_view(), name="blog-failed-url-detail"),
    # 配置
    path("config/", BlogConfigView.as_view(), name="blog-config"),
    path("config/dimensions/", ScoreDimensionListCreateView.as_view(), name="blog-score-dimensions"),
    path("config/dimensions/<int:pk>/", ScoreDimensionDetailView.as_view(), name="blog-score-dimension-detail"),
    # 调度
    path("scheduler/status/", SchedulerStatusView.as_view(), name="blog-scheduler-status"),
    path("scheduler/fetch_all/", FetchAllView.as_view(), name="blog-fetch-all"),
]
