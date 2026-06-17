from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import UserRole


class IsShopMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.shop_id)


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.role == UserRole.ADMIN)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in {UserRole.ADMIN, UserRole.MANAGER}
        )


class ClientPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not IsShopMember().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        return IsAdminOrManager().has_permission(request, view)

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.shop_id != request.user.shop_id:
            return False
        if request.method in SAFE_METHODS:
            return True
        return IsAdminOrManager().has_permission(request, view)


class OrderPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not IsShopMember().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        return IsAdminOrManager().has_permission(request, view)

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.shop_id != request.user.shop_id:
            return False
        if request.method in SAFE_METHODS:
            return True
        return IsAdminOrManager().has_permission(request, view)


class ChatPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        return IsShopMember().has_permission(request, view)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if obj.shop_id != user.shop_id:
            return False
        if user.role == UserRole.SUPPORT_MANAGER:
            return obj.assigned_to_id == user.id
        return True
