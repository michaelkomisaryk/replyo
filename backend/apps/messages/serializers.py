from rest_framework import serializers

from apps.messages.models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(
        source="client.instagram_username",
        read_only=True,
    )
    client_display_name = serializers.CharField(
        source="client.display_name",
        read_only=True,
    )

    class Meta:
        model = Chat
        fields = [
            "id",
            "shop",
            "client",
            "client_username",
            "client_display_name",
            "assigned_to",
            "priority",
            "created_at",
            "updated_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "chat",
            "direction",
            "content",
            "sent_at",
            "external_id",
            "delivery_status",
            "delivery_error",
            "created_at",
            "updated_at",
        ]


class ChatReplySerializer(serializers.Serializer):
    content = serializers.CharField(max_length=1000)
