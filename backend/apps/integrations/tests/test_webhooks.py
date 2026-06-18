import hashlib
import hmac
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.integrations.inbound_sync import process_unhandled_webhook_events
from apps.integrations.instagram_oauth import connect_mock_account
from apps.integrations.models import InstagramWebhookEvent
from apps.integrations.webhooks import build_mock_webhook_payload, dumps_payload
from apps.messages.models import Chat, Message


@override_settings(
    DEBUG=True,
    META_APP_ID="",
    META_APP_SECRET="",
    META_WEBHOOK_VERIFY_TOKEN="replyo-test-token",
)
class InstagramWebhookTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Webhook Shop")
        self.admin = User.objects.create_user(
            username="admin@webhook.com",
            email="admin@webhook.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.connection = connect_mock_account(shop=self.shop, connected_by=self.admin)
        self.client = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _sign_payload(self, payload: dict, secret: str = "test-secret") -> tuple[str, bytes]:
        body = dumps_payload(payload)
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return f"sha256={digest}", body

    def test_webhook_verification_returns_challenge(self):
        response = self.client.get(
            "/api/integrations/instagram/webhook/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "replyo-test-token",
                "hub.challenge": "1234567890",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "1234567890")

    def test_inbound_webhook_creates_chat_and_message(self):
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_001",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.001",
            text="Hello from Instagram",
            sender_username="beauty_buyer",
        )
        response = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Chat.objects.count(), 1)
        self.assertEqual(Client.objects.count(), 1)

        client = Client.objects.get()
        self.assertEqual(client.instagram_username, "beauty_buyer")
        self.assertEqual(client.instagram_user_id, "customer_ig_001")

        message = Message.objects.get()
        self.assertEqual(message.external_id, "mid.webhook.001")
        self.assertEqual(message.content, "Hello from Instagram")
        self.assertEqual(message.direction, "inbound")

    def test_duplicate_webhook_is_idempotent(self):
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_002",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.duplicate",
            text="First message",
            sender_username="repeat_user",
        )

        first = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=payload,
            format="json",
        )
        second = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=payload,
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(InstagramWebhookEvent.objects.count(), 1)

    def test_links_existing_client_by_instagram_username(self):
        existing = Client.objects.create(
            shop=self.shop,
            instagram_username="known_client",
            display_name="Known Client",
        )
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_003",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.link",
            text="Do you have this in stock?",
            sender_username="known_client",
        )

        response = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Client.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.instagram_user_id, "customer_ig_003")
        self.assertEqual(Chat.objects.get().client_id, existing.id)

    def test_messages_available_via_api_immediately(self):
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_004",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.api",
            text="API visibility test",
            sender_username="api_user",
        )
        self.client.post(
            "/api/integrations/instagram/webhook/",
            data=payload,
            format="json",
        )

        self._auth(self.admin)
        response = self.client.get("/api/messages/")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "API visibility test")

    @override_settings(META_APP_SECRET="test-secret", DEBUG=False)
    def test_invalid_signature_is_rejected(self):
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_005",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.sig",
            text="Signed payload",
            sender_username="signed_user",
        )
        body = dumps_payload(payload)

        response = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256="sha256=invalid",
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(META_APP_SECRET="test-secret", DEBUG=False)
    def test_valid_signature_is_accepted(self):
        payload = build_mock_webhook_payload(
            shop_instagram_id=self.connection.instagram_user_id,
            sender_id="customer_ig_006",
            recipient_id=self.connection.page_id,
            message_id="mid.webhook.validsig",
            text="Signed ok",
            sender_username="signed_ok",
        )
        signature, body = self._sign_payload(payload, secret="test-secret")

        response = self.client.post(
            "/api/integrations/instagram/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=signature,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)

    def test_sync_command_processes_queued_events(self):
        InstagramWebhookEvent.objects.create(
            shop=self.shop,
            event_id="queued:event:001",
            payload={
                "message_id": "mid.queued.001",
                "sender_id": "customer_ig_007",
                "text": "Queued message",
                "sender_username": "queued_user",
                "timestamp_ms": 1_700_000_000_000,
            },
        )

        processed = process_unhandled_webhook_events()
        self.assertEqual(processed, 1)
        event = InstagramWebhookEvent.objects.get(event_id="queued:event:001")
        self.assertIsNotNone(event.processed_at)
        self.assertEqual(Message.objects.get().external_id, "mid.queued.001")
