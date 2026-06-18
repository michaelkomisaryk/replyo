from rest_framework import viewsets

from apps.accounts.models import Shop, User, UserRole
from apps.accounts.serializers import ShopSerializer, UserSerializer
from apps.common.permissions import IsShopMember
from apps.common.viewsets import ShopQuerysetMixin


class ShopViewSet(ShopQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Shop.objects.all().order_by("name")
    serializer_class = ShopSerializer
    permission_classes = [IsShopMember]


class UserViewSet(ShopQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related("shop").all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsShopMember]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return queryset
        if (
            user.role == UserRole.MANAGER
            and self.request.query_params.get("team") == "1"
        ):
            return queryset
        return queryset.filter(pk=user.pk)
