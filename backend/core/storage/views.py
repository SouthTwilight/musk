from rest_framework import generics, parsers
from core.storage.models import UploadedFile
from core.storage.serializers import UploadedFileSerializer


class FileListView(generics.ListCreateAPIView):
    serializer_class = UploadedFileSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            filename=self.request.FILES["file"].name,
        )


class FileDetailView(generics.DestroyAPIView):
    serializer_class = UploadedFileSerializer

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)
