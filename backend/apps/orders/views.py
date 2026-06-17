from rest_framework import viewsets

from apps.common.permissions import OrderPermission
from apps.common.viewsets import ShopQuerysetMixin
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer


class OrderViewSet(ShopQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Order.objects.select_related("shop", "client", "chat")
        .all()
        .order_by("-created_at")
    )
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)
