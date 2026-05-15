from django.urls import path
from core.storage.views import FileListView, FileDetailView

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("<int:pk>/", FileDetailView.as_view(), name="file-detail"),
]
