from rest_framework import serializers

from apps.messages.models import Chat, ChatNotification, Message
from apps.messages.priority import get_wait_seconds, get_wait_urgency


class ChatSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(
        source="client.instagram_username",
        read_only=True,
    )
    client_display_name = serializers.CharField(
        source="client.display_name",
        read_only=True,
    )
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    wait_seconds = serializers.SerializerMethodField()
    wait_urgency = serializers.SerializerMethodField()

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
            "priority_label",
            "is_pinned",
            "is_archived",
            "archived_at",
            "has_new_message_badge",
            "wait_seconds",
            "wait_urgency",
            "created_at",
            "updated_at",
        ]

    def get_wait_seconds(self, chat: Chat) -> int | None:
        return get_wait_seconds(chat)

    def get_wait_urgency(self, chat: Chat) -> str | None:
        return get_wait_urgency(chat)


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


class ChatNotificationSerializer(serializers.ModelSerializer):
    chat_id = serializers.IntegerField(source="chat.id", read_only=True)
    client_username = serializers.CharField(
        source="chat.client.instagram_username",
        read_only=True,
    )

    class Meta:
        model = ChatNotification
        fields = [
            "id",
            "chat_id",
            "client_username",
            "kind",
            "message",
            "is_read",
            "created_at",
        ]
