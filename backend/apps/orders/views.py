from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.common.permissions import IsAdminOrManager, IsShopMember, OrderPermission
from apps.common.viewsets import ShopQuerysetMixin
from apps.messages.models import Chat
from apps.orders.models import Order, OrderStatus
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusChangeSerializer,
    OrderStatusUpdateSerializer,
)
from apps.orders.services import create_order_for_chat, update_order_status


class OrderViewSet(ShopQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Order.objects.select_related("shop", "client", "chat")
        .all()
        .order_by("-created_at")
    )
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get("client")
        chat_id = self.request.query_params.get("chat")
        status_filter = self.request.query_params.get("status")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_id = request.data.get("chat")
        client_id = request.data.get("client")
        if not chat_id or not client_id:
            return Response(
                {"detail": "Both chat and client are required to create an order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat = get_object_or_404(
            Chat.objects.filter(shop=request.user.shop),
            id=chat_id,
            client_id=client_id,
        )
        order = create_order_for_chat(
            chat=chat,
            created_by=request.user,
            status=serializer.validated_data.get(
                "status",
                OrderStatus.NEW_CLIENT,
            ),
        )
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = update_order_status(
            order=order,
            new_status=serializer.validated_data["status"],
            changed_by=request.user,
        )
        return Response(OrderSerializer(order).data)


class ChatCreateOrderView(APIView):
    permission_classes = [IsAdminOrManager, IsShopMember]

    def post(self, request, chat_id: int):
        chats = Chat.objects.select_related("client", "shop").filter(
            shop=request.user.shop
        )
        if request.user.role == UserRole.SUPPORT_MANAGER:
            chats = chats.filter(assigned_to=request.user)

        chat = get_object_or_404(chats, id=chat_id)

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order_for_chat(
            chat=chat,
            created_by=request.user,
            status=serializer.validated_data.get("status", "new_client"),
        )
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderStatusHistoryView(APIView):
    permission_classes = [IsShopMember]

    def get(self, request, order_id: int):
        order = get_object_or_404(
            Order.objects.filter(shop=request.user.shop),
            id=order_id,
        )
        changes = order.status_changes.all()
        return Response(OrderStatusChangeSerializer(changes, many=True).data)
