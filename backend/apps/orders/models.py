from django.db import models

from apps.common.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    NEW_CLIENT = "new_client", "New Client"
    WAITING_PAYMENT = "waiting_payment", "Waiting Payment"
    PAID = "paid", "Paid"
    SENT = "sent", "Sent"
    COMPLETED = "completed", "Completed"
    REJECTED = "rejected", "Rejected"


class Order(TimeStampedModel):
    shop = models.ForeignKey(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    chat = models.ForeignKey(
        "crm_messages.Chat",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW_CLIENT,
    )

    class Meta:
        indexes = [
            models.Index(fields=["shop", "status"]),
            models.Index(fields=["client"]),
            models.Index(fields=["chat"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.pk} ({self.get_status_display()})"
