from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class InstagramConnection(TimeStampedModel):
    shop = models.OneToOneField(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="instagram_connection",
    )
    instagram_user_id = models.CharField(max_length=64)
    instagram_username = models.CharField(max_length=255)
    page_id = models.CharField(max_length=64, blank=True, default="")
    encrypted_access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instagram_connections_created",
    )

    class Meta:
        indexes = [
            models.Index(fields=["instagram_user_id"]),
        ]

    def __str__(self) -> str:
        return f"@{self.instagram_username} ({self.shop.name})"
