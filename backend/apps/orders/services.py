from __future__ import annotations

from apps.messages.models import Chat
from apps.orders.models import Order, OrderStatus, OrderStatusChange

from apps.messages.priority import recalculate_chat_priority as _recalculate_chat_priority


def sync_chat_priority(chat: Chat) -> Chat:
    return _recalculate_chat_priority(chat)


def create_order_for_chat(
    *,
    chat: Chat,
    created_by,
    status: str = OrderStatus.NEW_CLIENT,
) -> Order:
    order = Order.objects.create(
        shop=chat.shop,
        client=chat.client,
        chat=chat,
        status=status,
    )
    OrderStatusChange.objects.create(
        order=order,
        from_status="",
        to_status=status,
        changed_by=created_by,
    )
    sync_chat_priority(chat)
    return order


def update_order_status(*, order: Order, new_status: str, changed_by) -> Order:
    previous_status = order.status
    if previous_status == new_status:
        return order

    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    OrderStatusChange.objects.create(
        order=order,
        from_status=previous_status,
        to_status=new_status,
        changed_by=changed_by,
    )

    if order.chat_id:
        sync_chat_priority(order.chat)

    return order
