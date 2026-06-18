from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Chat(TimeStampedModel):
    shop = models.ForeignKey(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="chats",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="chats",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_chats",
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["shop", "client"]),
            models.Index(fields=["shop", "assigned_to"]),
        ]

    def __str__(self) -> str:
        return f"Chat with {self.client}"


class MessageDirection(models.TextChoices):
    INBOUND = "inbound", "Inbound"
    OUTBOUND = "outbound", "Outbound"


class MessageDeliveryStatus(models.TextChoices):
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Message(TimeStampedModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    direction = models.CharField(max_length=16, choices=MessageDirection.choices)
    content = models.TextField()
    sent_at = models.DateTimeField()
    external_id = models.CharField(max_length=255, blank=True)
    delivery_status = models.CharField(
        max_length=16,
        choices=MessageDeliveryStatus.choices,
        blank=True,
        default="",
    )
    delivery_error = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["chat", "sent_at"]),
            models.Index(fields=["direction"]),
            models.Index(fields=["external_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["external_id"],
                condition=models.Q(external_id__gt=""),
                name="unique_message_external_id",
            ),
        ]
        ordering = ["sent_at"]

    def __str__(self) -> str:
        return f"{self.direction} message at {self.sent_at}"
