from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.common.permissions import ChatPermission, IsAdminOrManager, IsShopMember
from apps.common.viewsets import ChatQuerysetMixin
from apps.integrations.outbound_sync import OutboundSendError, send_chat_reply
from apps.messages.models import Chat, ChatNotification, Message
from apps.messages.priority import build_priority_buckets, get_waiting_reply_threshold
from apps.messages.serializers import (
    ChatReplySerializer,
    ChatSerializer,
    ChatNotificationSerializer,
    MessageSerializer,
)
from apps.messages.visibility import (
    archive_chat,
    filter_chats_for_view,
    search_archived_chats,
)


class ChatViewSet(ChatQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Chat.objects.select_related("shop", "client", "assigned_to")
        .all()
        .order_by("-updated_at")
    )
    serializer_class = ChatSerializer
    permission_classes = [ChatPermission]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        view = self.request.query_params.get("view", "active")
        queryset = filter_chats_for_view(queryset, view)

        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)


class ChatPrioritiesView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get(self, request):
        chats = Chat.objects.select_related("client", "assigned_to").filter(
            shop=request.user.shop
        )
        if request.user.role == UserRole.SUPPORT_MANAGER:
            chats = chats.filter(assigned_to=request.user)

        chats = filter_chats_for_view(chats, "active")

        buckets = build_priority_buckets(chats)
        serialized_buckets = []
        for bucket in buckets:
            serialized_buckets.append(
                {
                    "priority": bucket["priority"],
                    "label": bucket["label"],
                    "count": bucket["count"],
                    "chats": ChatSerializer(
                        bucket["chats"],
                        many=True,
                        context={"request": request},
                    ).data,
                }
            )

        threshold = get_waiting_reply_threshold()
        return Response(
            {
                "wait_threshold_seconds": int(threshold.total_seconds()),
                "buckets": serialized_buckets,
            }
        )


class MessageViewSet(ChatQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related("chat").all().order_by("sent_at")
    serializer_class = MessageSerializer
    permission_classes = [ChatPermission]
    shop_field = "chat__shop"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == UserRole.SUPPORT_MANAGER:
            queryset = queryset.filter(chat__assigned_to=user)

        chat_id = self.request.query_params.get("chat")
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset


class ChatReplyView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def post(self, request, chat_id: int):
        chats = Chat.objects.select_related("client", "shop").filter(
            shop=request.user.shop
        )
        if request.user.role == UserRole.SUPPORT_MANAGER:
            chats = chats.filter(assigned_to=request.user)

        chat = get_object_or_404(chats, id=chat_id)

        serializer = ChatReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            message = send_chat_reply(
                chat=chat,
                content=serializer.validated_data["content"],
            )
        except OutboundSendError as exc:
            status_code = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if exc.status_code == 429
                else status.HTTP_400_BAD_REQUEST
            )
            payload = {"detail": exc.message}
            if exc.retryable:
                payload["retryable"] = True

            failed_message = (
                Message.objects.filter(
                    chat=chat,
                    direction="outbound",
                    delivery_status="failed",
                )
                .order_by("-created_at")
                .first()
            )
            if failed_message:
                payload["message"] = MessageSerializer(failed_message).data

            return Response(payload, status=status_code)

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class ChatArchiveSearchView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get(self, request):
        query = request.query_params.get("q", "")
        chats = search_archived_chats(shop=request.user.shop, query=query)
        if request.user.role == UserRole.SUPPORT_MANAGER:
            chats = chats.filter(assigned_to=request.user)

        return Response(
            ChatSerializer(chats, many=True, context={"request": request}).data
        )


class ChatPinView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request, chat_id: int):
        chat = get_object_or_404(
            Chat.objects.filter(shop=request.user.shop),
            id=chat_id,
        )
        pinned = request.data.get("pinned", True)
        chat.is_pinned = bool(pinned)
        chat.save(update_fields=["is_pinned", "updated_at"])
        return Response(ChatSerializer(chat, context={"request": request}).data)


class ChatArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request, chat_id: int):
        chat = get_object_or_404(
            Chat.objects.filter(shop=request.user.shop),
            id=chat_id,
        )
        archive_chat(chat)
        return Response(ChatSerializer(chat, context={"request": request}).data)


class ChatNotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsShopMember]

    def get(self, request):
        notifications = ChatNotification.objects.select_related("chat", "chat__client").filter(
            user=request.user,
        )
        unread_only = request.query_params.get("unread")
        if unread_only in {"1", "true", "yes"}:
            notifications = notifications.filter(is_read=False)

        return Response(
            ChatNotificationSerializer(notifications[:50], many=True).data
        )
