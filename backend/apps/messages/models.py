from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Chat(TimeStampedModel):
    class Priority(models.TextChoices):
        NEW_CLIENTS = "new_clients", "New Clients"
        WAITING_REPLY = "waiting_reply", "Waiting for Reply"
        ACTIVE_ORDERS = "active_orders", "Active Orders"
        COMPLETED_ORDERS = "completed_orders", "Completed Orders"
        REJECTED = "rejected", "Rejected Clients"

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
    priority = models.CharField(
        max_length=32,
        choices=Priority.choices,
        default=Priority.NEW_CLIENTS,
    )
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    has_new_message_badge = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["shop", "client"]),
            models.Index(fields=["shop", "assigned_to"]),
            models.Index(fields=["shop", "priority"]),
            models.Index(fields=["shop", "is_archived"]),
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


class ChatNotification(TimeStampedModel):
    class Kind(models.TextChoices):
        CHAT_REACTIVATED = "chat_reactivated", "Chat Reactivated"

    shop = models.ForeignKey(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="chat_notifications",
    )
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_notifications",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["shop", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind} for chat {self.chat_id}"
