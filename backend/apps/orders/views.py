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

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get("client")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)
