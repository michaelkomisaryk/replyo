from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.integrations.inbound_sync import ingest_inbound_message
from apps.integrations.webhooks import InboundInstagramMessage
from apps.integrations.models import InstagramConnection
from apps.messages.models import Chat, ChatNotification, Message, MessageDirection
from apps.messages.visibility import (
    archive_chat,
    archive_stale_chats,
    is_chat_active,
    should_show_in_active_view,
)
from apps.orders.models import Order, OrderStatus
from apps.orders.services import update_order_status


@override_settings(
    CHAT_ACTIVE_MESSAGE_WINDOW_DAYS=7,
    CHAT_COMPLETED_VISIBLE_HOURS=24,
)
class ChatVisibilityTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Visibility Shop")
        self.admin = User.objects.create_user(
            username="admin@visibility.com",
            email="admin@visibility.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@visibility.com",
            email="manager@visibility.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="visible_client",
            display_name="Visible Client",
        )
        self.chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.manager,
        )
        self.api = APIClient()
        self.now = timezone.now()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _add_message(self, *, days_ago: int = 0, direction=MessageDirection.INBOUND):
        Message.objects.create(
            chat=self.chat,
            direction=direction,
            content="hello",
            sent_at=self.now - timedelta(days=days_ago),
        )

    def test_stale_chat_is_inactive(self):
        self._add_message(days_ago=8)
        self.assertFalse(is_chat_active(self.chat, now=self.now))
        self.assertFalse(should_show_in_active_view(self.chat, now=self.now))

    def test_recent_message_keeps_chat_active(self):
        self._add_message(days_ago=2)
        self.assertTrue(is_chat_active(self.chat, now=self.now))

    def test_pinned_chat_stays_active_without_recent_messages(self):
        self._add_message(days_ago=30)
        self.chat.is_pinned = True
        self.chat.save(update_fields=["is_pinned"])
        self.assertTrue(is_chat_active(self.chat, now=self.now))

    def test_open_order_keeps_chat_active(self):
        self._add_message(days_ago=30)
        Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.PAID,
        )
        self.assertTrue(is_chat_active(self.chat, now=self.now))

    def test_completed_order_visible_for_24_hours(self):
        self._add_message(days_ago=30)
        order = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.COMPLETED,
            completed_at=self.now - timedelta(hours=12),
        )
        self.chat.priority = Chat.Priority.COMPLETED_ORDERS
        self.chat.save(update_fields=["priority"])
        self.assertTrue(is_chat_active(self.chat, now=self.now))
        self.assertTrue(should_show_in_active_view(self.chat, now=self.now))

        order.completed_at = self.now - timedelta(hours=25)
        order.save(update_fields=["completed_at"])
        self.assertFalse(is_chat_active(self.chat, now=self.now))

    def test_rejected_chat_hidden_from_active_view(self):
        self._add_message(days_ago=1)
        self.chat.priority = Chat.Priority.REJECTED
        self.chat.save(update_fields=["priority"])
        self.assertFalse(should_show_in_active_view(self.chat, now=self.now))

    def test_auto_archive_completed_order_after_24_hours(self):
        self._add_message(days_ago=30)
        Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.COMPLETED,
            completed_at=self.now - timedelta(hours=25),
        )
        archived = archive_stale_chats(shop=self.shop, now=self.now)
        self.chat.refresh_from_db()
        self.assertEqual(archived, 1)
        self.assertTrue(self.chat.is_archived)

    def test_inbound_message_reactivates_archived_chat_and_notifies(self):
        archive_chat(self.chat, now=self.now)
        InstagramConnection.objects.create(
            shop=self.shop,
            instagram_user_id="shop_ig",
            page_id="page_1",
            encrypted_access_token="mock_token_test",
            instagram_username="shop",
        )
        inbound = InboundInstagramMessage(
            event_id="evt-reactivate",
            shop_instagram_id="shop_ig",
            sender_id=self.client_record.instagram_user_id or "sender_1",
            recipient_id="page_1",
            message_id="msg-reactivate",
            text="Are you there?",
            timestamp_ms=int(self.now.timestamp() * 1000),
            sender_username=self.client_record.instagram_username,
        )
        self.client_record.instagram_user_id = "sender_1"
        self.client_record.save(update_fields=["instagram_user_id"])

        ingest_inbound_message(inbound, store_event=False)

        self.chat.refresh_from_db()
        self.assertFalse(self.chat.is_archived)
        self.assertTrue(self.chat.has_new_message_badge)
        notifications = ChatNotification.objects.filter(chat=self.chat)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().user_id, self.manager.id)

    def test_active_view_api_hides_inactive_chats(self):
        active_chat = self.chat
        self._add_message(days_ago=1)

        stale_client = Client.objects.create(
            shop=self.shop,
            instagram_username="stale_client",
            display_name="Stale Client",
        )
        stale_chat = Chat.objects.create(shop=self.shop, client=stale_client)
        Message.objects.create(
            chat=stale_chat,
            direction=MessageDirection.INBOUND,
            content="old",
            sent_at=self.now - timedelta(days=10),
        )

        self._auth(self.admin)
        response = self.api.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        self.assertIn(active_chat.id, ids)
        self.assertNotIn(stale_chat.id, ids)

    def test_rejected_view_api(self):
        self.chat.priority = Chat.Priority.REJECTED
        self.chat.save(update_fields=["priority"])
        self._add_message(days_ago=1)

        self._auth(self.admin)
        response = self.api.get("/api/chats/?view=rejected")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.chat.id)

    def test_archive_search_api(self):
        archive_chat(self.chat, now=self.now)
        self._auth(self.admin)
        response = self.api.get("/api/chats/archive/search/?q=visible")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.chat.id)

    def test_manual_archive_endpoint(self):
        self._auth(self.manager)
        response = self.api.post(f"/api/chats/{self.chat.id}/archive/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_archived)

    def test_completed_at_set_on_order_completion(self):
        order = Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.SENT,
        )
        update_order_status(order=order, new_status=OrderStatus.COMPLETED, changed_by=self.admin)
        order.refresh_from_db()
        self.assertIsNotNone(order.completed_at)

    def test_notifications_api_lists_reactivation(self):
        ChatNotification.objects.create(
            shop=self.shop,
            chat=self.chat,
            user=self.manager,
            kind=ChatNotification.Kind.CHAT_REACTIVATED,
            message="Chat reactivated",
        )
        self._auth(self.manager)
        response = self.api.get("/api/notifications/?unread=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
