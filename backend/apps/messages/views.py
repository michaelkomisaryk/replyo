from rest_framework import viewsets

from apps.messages.models import Chat, Message
from apps.messages.serializers import ChatSerializer, MessageSerializer


class ChatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Chat.objects.select_related("shop", "client", "assigned_to")
        .all()
        .order_by("-updated_at")
    )
    serializer_class = ChatSerializer


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related("chat").all().order_by("sent_at")
    serializer_class = MessageSerializer
