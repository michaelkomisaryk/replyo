from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.orders.models import Order, OrderStatus


class ClientCardTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Card Shop")
        self.admin = User.objects.create_user(
            username="admin@card.com",
            email="admin@card.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@card.com",
            email="manager@card.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.support = User.objects.create_user(
            username="support@card.com",
            email="support@card.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="card_client",
            instagram_user_id="ig_card_001",
            display_name="Card Client",
            notes="Prefers morning delivery",
        )
        self.order_one = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            status=OrderStatus.WAITING_PAYMENT,
        )
        self.order_two = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            status=OrderStatus.COMPLETED,
        )
        self.api = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_client_card_shows_profile_and_orders(self):
        self._auth(self.admin)
        response = self.api.get(f"/api/clients/{self.client_record.id}/card/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["instagram_username"], "card_client")
        self.assertEqual(payload["notes"], "Prefers morning delivery")
        self.assertTrue(payload["can_edit"])
        self.assertEqual(len(payload["orders"]), 2)
        statuses = {order["status"] for order in payload["orders"]}
        self.assertEqual(
            statuses,
            {OrderStatus.WAITING_PAYMENT, OrderStatus.COMPLETED},
        )

    def test_manager_can_update_notes_on_card(self):
        self._auth(self.manager)
        response = self.api.patch(
            f"/api/clients/{self.client_record.id}/card/",
            {"notes": "Updated notes from manager"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.notes, "Updated notes from manager")
        self.assertEqual(response.json()["notes"], "Updated notes from manager")

    def test_support_manager_can_read_card_but_not_edit(self):
        self._auth(self.support)
        response = self.api.get(f"/api/clients/{self.client_record.id}/card/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["can_edit"])

        patch_response = self.api.patch(
            f"/api/clients/{self.client_record.id}/card/",
            {"notes": "Support should not save this"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.notes, "Prefers morning delivery")

    def test_orders_include_status_labels(self):
        self._auth(self.admin)
        response = self.api.get(f"/api/clients/{self.client_record.id}/card/")
        order = next(
            item
            for item in response.json()["orders"]
            if item["status"] == OrderStatus.WAITING_PAYMENT
        )
        self.assertEqual(order["status_label"], "Waiting Payment")
