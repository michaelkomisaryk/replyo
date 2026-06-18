from __future__ import annotations

from django.db.models import Prefetch, Q

from apps.accounts.models import UserRole
from apps.clients.models import Client
from apps.messages.models import Chat


def search_clients(*, shop, user, query: str, limit: int = 25) -> list[dict]:
    normalized = query.strip().lstrip("@")
    queryset = Client.objects.filter(shop=shop).prefetch_related(
        Prefetch(
            "chats",
            queryset=Chat.objects.select_related("assigned_to")
            .filter(shop=shop)
            .order_by("-updated_at"),
        )
    )

    if normalized:
        queryset = queryset.filter(
            Q(instagram_username__icontains=normalized)
            | Q(display_name__icontains=normalized)
        )

    if user.role == UserRole.SUPPORT_MANAGER:
        queryset = queryset.filter(chats__assigned_to=user).distinct()

    results: list[dict] = []
    for client in queryset.order_by("instagram_username")[:limit]:
        chat = next(iter(client.chats.all()), None)
        results.append(
            {
                "id": client.id,
                "instagram_username": client.instagram_username,
                "display_name": client.display_name,
                "chat_id": chat.id if chat else None,
                "is_archived": chat.is_archived if chat else False,
                "assigned_to_email": chat.assigned_to.email
                if chat and chat.assigned_to_id
                else None,
            }
        )

    return results
