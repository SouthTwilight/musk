from rest_framework import generics
from core.config.models import UserConfig
from core.config.serializers import UserConfigSerializer


class MyConfigView(generics.RetrieveUpdateAPIView):
    serializer_class = UserConfigSerializer

    def get_object(self):
        config, _ = UserConfig.objects.get_or_create(user=self.request.user)
        return config
