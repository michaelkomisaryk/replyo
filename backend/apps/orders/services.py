from __future__ import annotations

from apps.messages.models import Chat
from apps.orders.models import Order, OrderStatus, OrderStatusChange

ACTIVE_ORDER_STATUSES = {
    OrderStatus.NEW_CLIENT,
    OrderStatus.WAITING_PAYMENT,
    OrderStatus.PAID,
    OrderStatus.SENT,
}


def sync_chat_priority(chat: Chat) -> Chat:
    latest_order = (
        Order.objects.filter(chat=chat).order_by("-updated_at", "-id").first()
    )
    if not latest_order:
        return chat

    if latest_order.status == OrderStatus.COMPLETED:
        chat.priority = Chat.Priority.COMPLETED_ORDERS
    elif latest_order.status == OrderStatus.REJECTED:
        chat.priority = Chat.Priority.REJECTED
    elif latest_order.status in ACTIVE_ORDER_STATUSES:
        chat.priority = Chat.Priority.ACTIVE_ORDERS

    chat.save(update_fields=["priority", "updated_at"])
    return chat


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
