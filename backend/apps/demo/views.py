from rest_framework import generics, serializers
from apps.demo.models import DemoItem


class DemoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoItem
        fields = ("id", "title", "content", "created_at")
        read_only_fields = ("id", "created_at")


class DemoItemListCreateView(generics.ListCreateAPIView):
    serializer_class = DemoItemSerializer

    def get_queryset(self):
        return DemoItem.objects.using(self._get_db()).all()

    def perform_create(self, serializer):
        serializer.save(using=self._get_db())

    def _get_db(self):
        from module_layer.registry import registry
        info = registry.get("demo")
        return info.db_alias if info else "default"
