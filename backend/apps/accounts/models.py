from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel


class Shop(TimeStampedModel):
    name = models.CharField(max_length=255)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    SUPPORT_MANAGER = "support_manager", "Support Manager"


class User(AbstractUser):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="members",
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.ADMIN,
    )
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["shop", "role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.username
