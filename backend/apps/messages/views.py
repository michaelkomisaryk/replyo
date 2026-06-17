from rest_framework import viewsets

from apps.accounts.models import UserRole
from apps.common.permissions import ChatPermission
from apps.common.viewsets import ChatQuerysetMixin
from apps.messages.models import Chat, Message
from apps.messages.serializers import ChatSerializer, MessageSerializer


class ChatViewSet(ChatQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Chat.objects.select_related("shop", "client", "assigned_to")
        .all()
        .order_by("-updated_at")
    )
    serializer_class = ChatSerializer
    permission_classes = [ChatPermission]
    http_method_names = ["get", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)


class MessageViewSet(ChatQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related("chat").all().order_by("sent_at")
    serializer_class = MessageSerializer
    permission_classes = [ChatPermission]
    shop_field = "chat__shop"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == UserRole.SUPPORT_MANAGER:
            return queryset.filter(chat__assigned_to=user)
        return queryset
