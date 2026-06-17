from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.messages.models import Chat
from apps.orders.models import Order, OrderStatus


class RolePermissionsTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Test Shop")
        self.other_shop = Shop.objects.create(name="Other Shop")

        self.admin = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@test.com",
            email="manager@test.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.support = User.objects.create_user(
            username="support@test.com",
            email="support@test.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )

        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="client_one",
            display_name="Client One",
            notes="VIP",
        )
        self.assigned_chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.support,
        )
        self.unassigned_chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.manager,
        )
        self.order = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.assigned_chat,
            status=OrderStatus.WAITING_PAYMENT,
        )

        self.client = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_admin_can_access_all_shop_chats(self):
        self._auth(self.admin)
        response = self.client.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_support_manager_only_sees_assigned_chats(self):
        self._auth(self.support)
        response = self.client.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chat_ids = {item["id"] for item in response.json()}
        self.assertEqual(chat_ids, {self.assigned_chat.id})

    def test_support_manager_cannot_access_unassigned_chat_detail(self):
        self._auth(self.support)
        response = self.client.get(f"/api/chats/{self.unassigned_chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_support_manager_can_read_client_cards(self):
        self._auth(self.support)
        response = self.client.get(f"/api/clients/{self.client_record.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_support_manager_cannot_update_client_cards(self):
        self._auth(self.support)
        response = self.client.patch(
            f"/api/clients/{self.client_record.id}/",
            {"notes": "Updated by support"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_update_client_cards(self):
        self._auth(self.manager)
        response = self.client.patch(
            f"/api/clients/{self.client_record.id}/",
            {"notes": "Updated by manager"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.notes, "Updated by manager")

    def test_support_manager_cannot_update_orders(self):
        self._auth(self.support)
        response = self.client.patch(
            f"/api/orders/{self.order.id}/",
            {"status": OrderStatus.PAID},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_update_orders(self):
        self._auth(self.manager)
        response = self.client.patch(
            f"/api/orders/{self.order.id}/",
            {"status": OrderStatus.PAID},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.PAID)

    def test_admin_can_list_all_orders(self):
        self._auth(self.admin)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
