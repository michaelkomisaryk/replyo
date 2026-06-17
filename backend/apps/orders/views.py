from rest_framework import viewsets

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Order.objects.select_related("shop", "client", "chat")
        .all()
        .order_by("-created_at")
    )
    serializer_class = OrderSerializer
