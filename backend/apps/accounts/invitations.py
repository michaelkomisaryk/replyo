import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.common.models import TimeStampedModel


class TeamInvitation(TimeStampedModel):
    shop = models.ForeignKey(
        "accounts.Shop",
        on_delete=models.CASCADE,
        related_name="team_invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=32,
        choices=[
            (UserRole.MANAGER, UserRole.MANAGER.label),
            (UserRole.SUPPORT_MANAGER, UserRole.SUPPORT_MANAGER.label),
        ],
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["shop", "email"]),
            models.Index(fields=["token"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_pending(self) -> bool:
        return self.accepted_at is None and not self.is_expired

    def __str__(self) -> str:
        return f"Invitation for {self.email} ({self.role})"
