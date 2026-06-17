from rest_framework import serializers

from apps.messages.models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = [
            "id",
            "shop",
            "client",
            "assigned_to",
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
            "created_at",
            "updated_at",
        ]
