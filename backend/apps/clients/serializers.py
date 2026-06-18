from rest_framework import serializers

from apps.clients.models import Client


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
