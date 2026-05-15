from django.urls import path
from core.config.views import MyConfigView

urlpatterns = [
    path("", MyConfigView.as_view(), name="my-config"),
]
