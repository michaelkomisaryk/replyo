from apps.accounts.models import UserRole


class ShopQuerysetMixin:
    shop_field = "shop"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated or not user.shop_id:
            return queryset.none()
        return queryset.filter(**{self.shop_field: user.shop})


class ChatQuerysetMixin(ShopQuerysetMixin):
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == UserRole.SUPPORT_MANAGER:
            return queryset.filter(assigned_to=user)
        return queryset
