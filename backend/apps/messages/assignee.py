from __future__ import annotations

from django.db.models import QuerySet

from apps.accounts.models import User, UserRole
from apps.messages.models import Chat, ChatNotification


def filter_chats_by_assignee(queryset: QuerySet, *, user, assigned_to: str | None):
    if not assigned_to:
        return queryset

    if user.role == UserRole.SUPPORT_MANAGER:
        return queryset

    if assigned_to == "me":
        return queryset.filter(assigned_to=user)

    if assigned_to == "unassigned":
        return queryset.filter(assigned_to__isnull=True)

    if user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        return queryset

    try:
        assignee_id = int(assigned_to)
    except (TypeError, ValueError):
        return queryset

    return queryset.filter(assigned_to_id=assignee_id)


def notify_chat_escalation(*, chat: Chat, escalated_by: User) -> list[ChatNotification]:
    client_label = chat.client.display_name or chat.client.instagram_username
    message = (
        f"{escalated_by.email} escalated the chat with {client_label} for manager review."
    )
    notifications: list[ChatNotification] = []

    for recipient in User.objects.filter(
        shop=chat.shop,
        role__in={UserRole.ADMIN, UserRole.MANAGER},
        is_active=True,
    ):
        notifications.append(
            ChatNotification.objects.create(
                shop=chat.shop,
                chat=chat,
                user=recipient,
                kind=ChatNotification.Kind.CHAT_ESCALATED,
                message=message,
            )
        )

    return notifications
