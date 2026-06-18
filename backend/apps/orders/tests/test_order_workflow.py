from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.messages.models import Chat
from apps.orders.models import Order, OrderStatus, OrderStatusChange


class OrderWorkflowTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Order Shop")
        self.admin = User.objects.create_user(
            username="admin@order.com",
            email="admin@order.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@order.com",
            email="manager@order.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.support = User.objects.create_user(
            username="support@order.com",
            email="support@order.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="order_client",
            display_name="Order Client",
        )
        self.chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.manager,
        )
        self.api = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_manager_can_create_order_from_chat(self):
        self._auth(self.manager)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/orders/",
            {"status": OrderStatus.WAITING_PAYMENT},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertEqual(payload["status"], OrderStatus.WAITING_PAYMENT)
        self.assertEqual(payload["chat"], self.chat.id)

        order = Order.objects.get()
        self.assertEqual(order.client_id, self.client_record.id)
        self.assertEqual(OrderStatusChange.objects.count(), 1)

    def test_support_manager_cannot_create_order(self):
        self._auth(self.support)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/orders/",
            {"status": OrderStatus.NEW_CLIENT},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_update_persists_and_logs_history(self):
        self._auth(self.manager)
        create_response = self.api.post(
            f"/api/chats/{self.chat.id}/orders/",
            {"status": OrderStatus.WAITING_PAYMENT},
            format="json",
        )
        order_id = create_response.json()["id"]

        patch_response = self.api.patch(
            f"/api/orders/{order_id}/",
            {"status": OrderStatus.PAID},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.json()["status"], OrderStatus.PAID)

        history_response = self.api.get(f"/api/orders/{order_id}/history/")
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        history = history_response.json()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["to_status"], OrderStatus.PAID)

    def test_completed_order_updates_chat_priority(self):
        self._auth(self.manager)
        create_response = self.api.post(
            f"/api/chats/{self.chat.id}/orders/",
            {"status": OrderStatus.SENT},
            format="json",
        )
        order_id = create_response.json()["id"]

        self.chat.refresh_from_db()
        self.assertEqual(self.chat.priority, Chat.Priority.ACTIVE_ORDERS)

        self.api.patch(
            f"/api/orders/{order_id}/",
            {"status": OrderStatus.COMPLETED},
            format="json",
        )
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.priority, Chat.Priority.COMPLETED_ORDERS)

    def test_orders_filterable_by_chat(self):
        self._auth(self.manager)
        self.api.post(
            f"/api/chats/{self.chat.id}/orders/",
            {"status": OrderStatus.NEW_CLIENT},
            format="json",
        )
        response = self.api.get(f"/api/orders/?chat={self.chat.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_support_manager_cannot_update_order_status(self):
        order = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.WAITING_PAYMENT,
        )
        self._auth(self.support)
        response = self.api.patch(
            f"/api/orders/{order.id}/",
            {"status": OrderStatus.PAID},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
