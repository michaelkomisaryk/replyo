from __future__ import annotations

from apps.accounts.models import UserRole


def filter_chats_by_assignee(queryset, *, user, assigned_to: str | None):

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
