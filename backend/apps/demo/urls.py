from django.urls import path
from apps.demo.views import DemoItemListCreateView

urlpatterns = [
    path("items/", DemoItemListCreateView.as_view(), name="demo-items"),
]
