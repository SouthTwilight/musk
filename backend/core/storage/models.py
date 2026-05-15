from django.db import models
from django.conf import settings


class UploadedFile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(upload_to="uploads/%Y%m/")
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "uploaded_file"
        ordering = ["-created_at"]
