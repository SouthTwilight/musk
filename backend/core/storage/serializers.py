from rest_framework import serializers
from core.storage.models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = ("id", "file", "filename", "url", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"filename": {"required": False}}

    def get_url(self, obj):
        request = self.context.get("request")
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None
