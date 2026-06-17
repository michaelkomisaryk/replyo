from django.db import models

from apps.common.models import TimeStampedModel


class Client(TimeStampedModel):
    shop = models.ForeignKey(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="clients",
    )
    instagram_username = models.CharField(max_length=150)
    display_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["shop", "instagram_username"]),
            models.Index(fields=["shop", "display_name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "instagram_username"],
                name="unique_client_instagram_per_shop",
            ),
        ]

    def __str__(self) -> str:
        return self.display_name or self.instagram_username
