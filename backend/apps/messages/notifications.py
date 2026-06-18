from __future__ import annotations

from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.messages.models import Chat, ChatNotification, Message, MessageDirection
from apps.messages.priority import calculate_chat_priority, get_waiting_reply_threshold


def get_notification_recipients(chat: Chat) -> list:
    if chat.assigned_to_id:
        return [chat.assigned_to]

    return list(
        User.objects.filter(
            shop=chat.shop,
            role__in={UserRole.ADMIN, UserRole.MANAGER},
            is_active=True,
        )
    )


def _client_label(chat: Chat) -> str:
    return chat.client.display_name or chat.client.instagram_username


def notify_new_inbound_message(chat: Chat) -> list[ChatNotification]:
    message = f"New message from {_client_label(chat)}."
    notifications: list[ChatNotification] = []

    for user in get_notification_recipients(chat):
        if ChatNotification.objects.filter(
            chat=chat,
            user=user,
            kind=ChatNotification.Kind.NEW_MESSAGE,
            is_read=False,
        ).exists():
            continue

        notifications.append(
            ChatNotification.objects.create(
                shop=chat.shop,
                chat=chat,
                user=user,
                kind=ChatNotification.Kind.NEW_MESSAGE,
                message=message,
            )
        )

    return notifications


def notify_chat_reactivation(chat: Chat) -> list[ChatNotification]:
    message = f"Archived chat with {_client_label(chat)} was reactivated by a new message."
    notifications: list[ChatNotification] = []

    for user in get_notification_recipients(chat):
        notifications.append(
            ChatNotification.objects.create(
                shop=chat.shop,
                chat=chat,
                user=user,
                kind=ChatNotification.Kind.CHAT_REACTIVATED,
                message=message,
            )
        )

    return notifications


def notify_chat_escalation(*, chat: Chat, escalated_by: User) -> list[ChatNotification]:
    message = (
        f"{escalated_by.email} escalated the chat with {_client_label(chat)} for manager review."
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


def send_waiting_reply_reminders(*, shop=None, now=None) -> int:
    now = now or timezone.now()
    threshold = get_waiting_reply_threshold()
    queryset = Chat.objects.select_related("client", "assigned_to").filter(
        is_archived=False,
    )
    if shop is not None:
        queryset = queryset.filter(shop=shop)

    created_count = 0
    for chat in queryset.iterator():
        if calculate_chat_priority(chat, now=now) != Chat.Priority.WAITING_REPLY:
            continue

        last_inbound = (
            Message.objects.filter(chat=chat, direction=MessageDirection.INBOUND)
            .order_by("-sent_at")
            .first()
        )
        if not last_inbound or now - last_inbound.sent_at < threshold:
            continue

        client_label = _client_label(chat)
        wait_minutes = int((now - last_inbound.sent_at).total_seconds() // 60)
        message = (
            f"{client_label} has been waiting for a reply for {wait_minutes} minutes."
        )

        for user in get_notification_recipients(chat):
            already_notified = ChatNotification.objects.filter(
                chat=chat,
                user=user,
                kind=ChatNotification.Kind.WAITING_REPLY_REMINDER,
                created_at__gte=last_inbound.sent_at,
            ).exists()
            if already_notified:
                continue

            ChatNotification.objects.create(
                shop=chat.shop,
                chat=chat,
                user=user,
                kind=ChatNotification.Kind.WAITING_REPLY_REMINDER,
                message=message,
            )
            created_count += 1

    return created_count
