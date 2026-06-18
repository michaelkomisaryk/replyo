from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.messages.models import Chat


class ClientSearchTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Search Shop")
        self.admin = User.objects.create_user(
            username="admin@search.com",
            email="admin@search.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.support = User.objects.create_user(
            username="support@search.com",
            email="support@search.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )
        self.active_client = Client.objects.create(
            shop=self.shop,
            instagram_username="active_shopper",
            display_name="Active Shopper",
        )
        self.archived_client = Client.objects.create(
            shop=self.shop,
            instagram_username="archived_buyer",
            display_name="Archived Buyer",
        )
        self.other_client = Client.objects.create(
            shop=self.shop,
            instagram_username="other_user",
            display_name="Other User",
        )
        self.active_chat = Chat.objects.create(
            shop=self.shop,
            client=self.active_client,
            assigned_to=self.support,
        )
        self.archived_chat = Chat.objects.create(
            shop=self.shop,
            client=self.archived_client,
            assigned_to=self.support,
            is_archived=True,
            archived_at=timezone.now(),
        )
        Chat.objects.create(
            shop=self.shop,
            client=self.other_client,
        )
        self.api = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_search_by_instagram_username(self):
        self._auth(self.admin)
        response = self.api.get("/api/clients/search/?q=active_shop")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["instagram_username"], "active_shopper")
        self.assertEqual(response.data[0]["chat_id"], self.active_chat.id)

    def test_search_by_display_name(self):
        self._auth(self.admin)
        response = self.api.get("/api/clients/search/?q=Archived")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["display_name"], "Archived Buyer")
        self.assertTrue(response.data[0]["is_archived"])

    def test_search_includes_archived_clients(self):
        self._auth(self.admin)
        response = self.api.get("/api/clients/search/?q=buyer")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["chat_id"], self.archived_chat.id)
        self.assertTrue(response.data[0]["is_archived"])

    def test_support_manager_only_sees_assigned_clients(self):
        self._auth(self.support)
        response = self.api.get("/api/clients/search/?q=user")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_short_query_returns_empty_list(self):
        self._auth(self.admin)
        response = self.api.get("/api/clients/search/?q=a")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
