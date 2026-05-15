from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Meta:
        db_table = "auth_user"
        verbose_name = "\u7528\u6237"
        verbose_name_plural = "\u7528\u6237"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)
