from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.integrations.instagram_oauth import connect_mock_account
from apps.integrations.outbound_sync import OutboundSendError
from apps.messages.models import Chat, Message, MessageDeliveryStatus, MessageDirection


@override_settings(DEBUG=True, META_APP_ID="", META_APP_SECRET="")
class ChatReplyTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Reply Shop")
        self.admin = User.objects.create_user(
            username="admin@reply.com",
            email="admin@reply.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@reply.com",
            email="manager@reply.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.support = User.objects.create_user(
            username="support@reply.com",
            email="support@reply.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )
        connect_mock_account(shop=self.shop, connected_by=self.admin)

        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="buyer_one",
            instagram_user_id="ig_buyer_001",
            display_name="Buyer One",
        )
        self.chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.support,
        )
        self.api = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_manager_can_send_reply(self):
        self._auth(self.manager)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/reply/",
            {"content": "Thanks for your order!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertEqual(payload["direction"], "outbound")
        self.assertEqual(payload["delivery_status"], "sent")
        self.assertTrue(payload["external_id"].startswith("mock_mid_"))

        message = Message.objects.get()
        self.assertEqual(message.content, "Thanks for your order!")
        self.assertEqual(message.delivery_status, MessageDeliveryStatus.SENT)

    def test_support_manager_can_reply_to_assigned_chat(self):
        self._auth(self.support)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/reply/",
            {"content": "Happy to help!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_support_manager_cannot_reply_to_unassigned_chat(self):
        other_chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.manager,
        )
        self._auth(self.support)
        response = self.api.post(
            f"/api/chats/{other_chat.id}/reply/",
            {"content": "Should fail"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_failed_send_returns_actionable_error(self):
        self._auth(self.admin)
        with patch(
            "apps.integrations.outbound_sync.send_instagram_text_message",
            side_effect=OutboundSendError(
                "Instagram rate limit reached. Please wait and try again.",
                retryable=True,
                status_code=429,
            ),
        ):
            response = self.api.post(
                f"/api/chats/{self.chat.id}/reply/",
                {"content": "Retry later"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        payload = response.json()
        self.assertTrue(payload["retryable"])
        self.assertIn("rate limit", payload["detail"].lower())
        self.assertEqual(payload["message"]["delivery_status"], "failed")

        failed = Message.objects.get()
        self.assertEqual(failed.delivery_status, MessageDeliveryStatus.FAILED)
        self.assertEqual(failed.direction, MessageDirection.OUTBOUND)

    def test_reply_without_instagram_connection_fails(self):
        self.shop.instagram_connection.delete()
        self._auth(self.admin)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/reply/",
            {"content": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Instagram is not connected", response.json()["detail"])

    def test_messages_filterable_by_chat(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Hi",
            sent_at=timezone.now(),
        )
        self._auth(self.admin)
        response = self.api.get(f"/api/messages/?chat={self.chat.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_empty_reply_is_rejected(self):
        self._auth(self.admin)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/reply/",
            {"content": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
