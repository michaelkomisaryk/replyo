from rest_framework import serializers

from apps.clients.models import Client
from apps.orders.models import Order


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "shop",
            "instagram_username",
            "instagram_user_id",
            "display_name",
            "notes",
            "created_at",
            "updated_at",
        ]


class ClientOrderSummarySerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "status_label",
            "chat",
            "created_at",
            "updated_at",
        ]


class ClientCardSerializer(serializers.ModelSerializer):
    orders = ClientOrderSummarySerializer(many=True, read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "shop",
            "instagram_username",
            "instagram_user_id",
            "display_name",
            "notes",
            "orders",
            "can_edit",
            "created_at",
            "updated_at",
        ]

    def get_can_edit(self, client: Client) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.accounts.models import UserRole

        return request.user.role in {UserRole.ADMIN, UserRole.MANAGER}


class ClientNotesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["notes"]


class ClientSearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    instagram_username = serializers.CharField()
    display_name = serializers.CharField()
    chat_id = serializers.IntegerField(allow_null=True)
    is_archived = serializers.BooleanField()
    assigned_to_email = serializers.CharField(allow_null=True)
