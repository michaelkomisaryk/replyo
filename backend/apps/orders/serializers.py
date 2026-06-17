from rest_framework import serializers

from apps.orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "shop",
            "client",
            "chat",
            "status",
            "created_at",
            "updated_at",
        ]
