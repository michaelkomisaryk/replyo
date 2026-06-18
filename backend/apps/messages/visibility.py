from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.messages.models import Chat, ChatNotification, Message
from apps.messages.notifications import (
    notify_chat_reactivation,
    notify_new_inbound_message,
)
from apps.messages.priority import ACTIVE_ORDER_STATUSES
from apps.orders.models import Order, OrderStatus


def get_active_message_window() -> timedelta:
    days = int(getattr(settings, "CHAT_ACTIVE_MESSAGE_WINDOW_DAYS", 7))
    return timedelta(days=days)


def get_completed_visible_window() -> timedelta:
    hours = int(getattr(settings, "CHAT_COMPLETED_VISIBLE_HOURS", 24))
    return timedelta(hours=hours)


def get_last_message_at(chat: Chat):
    return (
        Message.objects.filter(chat=chat).order_by("-sent_at").values_list("sent_at", flat=True).first()
    )


def has_recent_message(chat: Chat, *, now=None) -> bool:
    now = now or timezone.now()
    last_sent_at = get_last_message_at(chat)
    if not last_sent_at:
        return False
    return last_sent_at >= now - get_active_message_window()


def has_open_order(chat: Chat) -> bool:
    return Order.objects.filter(chat=chat, status__in=ACTIVE_ORDER_STATUSES).exists()


def get_latest_completed_at(chat: Chat):
    return (
        Order.objects.filter(chat=chat, status=OrderStatus.COMPLETED, completed_at__isnull=False)
        .order_by("-completed_at")
        .values_list("completed_at", flat=True)
        .first()
    )


def is_within_completed_visible_window(chat: Chat, *, now=None) -> bool:
    now = now or timezone.now()
    completed_at = get_latest_completed_at(chat)
    if not completed_at:
        return False
    return completed_at >= now - get_completed_visible_window()


def is_chat_active(chat: Chat, *, now=None) -> bool:
    if chat.is_pinned:
        return True
    if has_open_order(chat):
        return True
    if has_recent_message(chat, now=now):
        return True
    if is_within_completed_visible_window(chat, now=now):
        return True
    return False


def should_show_in_active_view(chat: Chat, *, now=None) -> bool:
    if chat.is_archived:
        return False
    if chat.priority == Chat.Priority.REJECTED and not chat.is_pinned:
        return False
    return is_chat_active(chat, now=now)


def filter_chats_for_view(queryset, view: str, *, now=None):
    now = now or timezone.now()
    view = (view or "active").lower()

    if view == "archived":
        return queryset.filter(is_archived=True)

    if view == "rejected":
        return queryset.filter(
            is_archived=False,
            priority=Chat.Priority.REJECTED,
        )

    if view == "all":
        return queryset

    return queryset.filter(is_archived=False).exclude(
        priority=Chat.Priority.REJECTED,
    ).filter(
        Q(is_pinned=True)
        | Q(
            id__in=Order.objects.filter(
                status__in=ACTIVE_ORDER_STATUSES,
                chat_id__isnull=False,
            ).values("chat_id")
        )
        | Q(
            id__in=Message.objects.filter(
                sent_at__gte=now - get_active_message_window(),
            ).values("chat_id")
        )
        | Q(
            id__in=Order.objects.filter(
                status=OrderStatus.COMPLETED,
                completed_at__gte=now - get_completed_visible_window(),
                chat_id__isnull=False,
            ).values("chat_id")
        )
    )


def archive_chat(chat: Chat, *, now=None) -> Chat:
    now = now or timezone.now()
    if chat.is_archived:
        return chat

    chat.is_archived = True
    chat.archived_at = now
    chat.has_new_message_badge = False
    chat.save(update_fields=["is_archived", "archived_at", "has_new_message_badge", "updated_at"])
    return chat


def reactivate_chat(chat: Chat) -> tuple[Chat, bool]:
    was_archived = chat.is_archived
    update_fields = ["updated_at"]

    if chat.is_archived:
        chat.is_archived = False
        chat.archived_at = None
        chat.has_new_message_badge = True
        update_fields.extend(["is_archived", "archived_at", "has_new_message_badge"])

    if len(update_fields) > 1:
        chat.save(update_fields=update_fields)

    return chat, was_archived


def handle_inbound_message_visibility(chat: Chat) -> list[ChatNotification]:
    chat, was_archived = reactivate_chat(chat)
    if was_archived:
        return notify_chat_reactivation(chat)
    return notify_new_inbound_message(chat)


def archive_stale_chats(*, shop=None, now=None) -> int:
    now = now or timezone.now()
    queryset = Chat.objects.filter(is_archived=False)
    if shop is not None:
        queryset = queryset.filter(shop=shop)

    archived_count = 0
    for chat in queryset.iterator():
        if chat.is_pinned:
            continue

        should_archive = False

        completed_at = get_latest_completed_at(chat)
        if completed_at and completed_at < now - get_completed_visible_window():
            should_archive = True
        elif not is_chat_active(chat, now=now):
            should_archive = True

        if should_archive:
            archive_chat(chat, now=now)
            archived_count += 1

    return archived_count


def search_archived_chats(*, shop, query: str):
    queryset = Chat.objects.select_related("client", "assigned_to").filter(
        shop=shop,
        is_archived=True,
    )
    if not query:
        return queryset.order_by("-archived_at", "-updated_at")

    normalized = query.strip().lstrip("@")
    if not normalized:
        return queryset.order_by("-archived_at", "-updated_at")

    return queryset.filter(
        Q(client__instagram_username__icontains=normalized)
        | Q(client__display_name__icontains=normalized)
    ).order_by("-archived_at", "-updated_at")
