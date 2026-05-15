from rest_framework import serializers
from core.config.models import UserConfig


class UserConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConfig
        fields = ("theme", "background_image", "sidebar_collapsed")
