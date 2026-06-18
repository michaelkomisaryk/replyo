from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.messages.models import Chat, Message, MessageDirection
from apps.orders.models import Order, OrderStatus

ACTIVE_ORDER_STATUSES = {
    OrderStatus.NEW_CLIENT,
    OrderStatus.WAITING_PAYMENT,
    OrderStatus.PAID,
    OrderStatus.SENT,
}

WAIT_URGENCY_THRESHOLDS = (
    ("red", timedelta(hours=4)),
    ("orange", timedelta(hours=2)),
    ("yellow", timedelta(hours=1)),
)


def get_waiting_reply_threshold() -> timedelta:
    seconds = int(
        getattr(settings, "CHAT_WAITING_REPLY_THRESHOLD_SECONDS", 3600)
    )
    return timedelta(seconds=seconds)


def _priority_from_orders(chat: Chat) -> str | None:
    latest_order = (
        Order.objects.filter(chat=chat).order_by("-updated_at", "-id").first()
    )
    if not latest_order:
        return None

    if latest_order.status == OrderStatus.COMPLETED:
        return Chat.Priority.COMPLETED_ORDERS
    if latest_order.status == OrderStatus.REJECTED:
        return Chat.Priority.REJECTED
    if latest_order.status in ACTIVE_ORDER_STATUSES:
        return Chat.Priority.ACTIVE_ORDERS
    return None


def _priority_from_messages(chat: Chat, *, now=None) -> str:
    now = now or timezone.now()
    messages = Message.objects.filter(chat=chat).order_by("sent_at")
    last_message = messages.order_by("-sent_at").first()
    if not last_message:
        return Chat.Priority.NEW_CLIENTS

    has_outbound = messages.filter(direction=MessageDirection.OUTBOUND).exists()
    if last_message.direction == MessageDirection.INBOUND:
        if not has_outbound:
            return Chat.Priority.NEW_CLIENTS

        wait_duration = now - last_message.sent_at
        if wait_duration >= get_waiting_reply_threshold():
            return Chat.Priority.WAITING_REPLY
        return Chat.Priority.NEW_CLIENTS

    return Chat.Priority.NEW_CLIENTS


def calculate_chat_priority(chat: Chat, *, now=None) -> str:
    order_priority = _priority_from_orders(chat)
    if order_priority:
        return order_priority
    return _priority_from_messages(chat, now=now)


def recalculate_chat_priority(chat: Chat, *, now=None) -> Chat:
    new_priority = calculate_chat_priority(chat, now=now)
    if chat.priority != new_priority:
        chat.priority = new_priority
        chat.save(update_fields=["priority", "updated_at"])
    return chat


def recalculate_shop_priorities(*, shop, now=None) -> int:
    updated = 0
    for chat in Chat.objects.filter(shop=shop):
        previous = chat.priority
        recalculate_chat_priority(chat, now=now)
        if chat.priority != previous:
            updated += 1
    return updated


def recalculate_all_priorities(*, now=None) -> int:
    updated = 0
    for chat in Chat.objects.all().iterator():
        previous = chat.priority
        recalculate_chat_priority(chat, now=now)
        if chat.priority != previous:
            updated += 1
    return updated


def get_last_inbound_wait_duration(chat: Chat, *, now=None):
    now = now or timezone.now()
    last_inbound = (
        Message.objects.filter(chat=chat, direction=MessageDirection.INBOUND)
        .order_by("-sent_at")
        .first()
    )
    if not last_inbound:
        return None
    return now - last_inbound.sent_at


def get_wait_urgency(chat: Chat, *, now=None) -> str | None:
    if chat.priority != Chat.Priority.WAITING_REPLY:
        return None

    wait_duration = get_last_inbound_wait_duration(chat, now=now)
    if wait_duration is None:
        return None

    for urgency, threshold in WAIT_URGENCY_THRESHOLDS:
        if wait_duration >= threshold:
            return urgency
    return "yellow"


def get_wait_seconds(chat: Chat, *, now=None) -> int | None:
    if chat.priority != Chat.Priority.WAITING_REPLY:
        return None
    wait_duration = get_last_inbound_wait_duration(chat, now=now)
    if wait_duration is None:
        return None
    return int(wait_duration.total_seconds())


def build_priority_buckets(chats) -> list[dict]:
    priority_order = [
        Chat.Priority.NEW_CLIENTS,
        Chat.Priority.WAITING_REPLY,
        Chat.Priority.ACTIVE_ORDERS,
        Chat.Priority.COMPLETED_ORDERS,
        Chat.Priority.REJECTED,
    ]
    chats_by_priority: dict[str, list] = {value: [] for value in priority_order}
    for chat in chats:
        chats_by_priority.setdefault(chat.priority, []).append(chat)

    return [
        {
            "priority": priority.value,
            "label": priority.label,
            "count": len(chats_by_priority.get(priority.value, [])),
            "chats": chats_by_priority.get(priority.value, []),
        }
        for priority in priority_order
    ]
