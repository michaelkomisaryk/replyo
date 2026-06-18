from rest_framework import serializers

from apps.orders.models import Order, OrderStatus, OrderStatusChange


class OrderStatusChangeSerializer(serializers.ModelSerializer):
    from_status_label = serializers.SerializerMethodField()
    to_status_label = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusChange
        fields = [
            "id",
            "from_status",
            "from_status_label",
            "to_status",
            "to_status_label",
            "changed_by",
            "created_at",
        ]

    def _status_label(self, value: str) -> str:
        if not value:
            return ""
        try:
            return OrderStatus(value).label
        except ValueError:
            return value

    def get_from_status_label(self, change: OrderStatusChange) -> str:
        return self._status_label(change.from_status)

    def get_to_status_label(self, change: OrderStatusChange) -> str:
        return self._status_label(change.to_status)


class OrderSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "shop",
            "client",
            "chat",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value: str) -> str:
        if value not in OrderStatus.values:
            raise serializers.ValidationError("Invalid order status.")
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)
