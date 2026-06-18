from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.integrations.inbound_sync import ingest_inbound_message
from apps.integrations.models import InstagramConnection
from apps.integrations.webhooks import InboundInstagramMessage
from apps.messages.models import Chat, ChatNotification, Message, MessageDirection
from apps.messages.notifications import send_waiting_reply_reminders


@override_settings(CHAT_WAITING_REPLY_THRESHOLD_SECONDS=3600)
class NotificationTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Notification Shop")
        self.admin = User.objects.create_user(
            username="admin@notify.com",
            email="admin@notify.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@notify.com",
            email="manager@notify.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="notify_client",
            display_name="Notify Client",
            instagram_user_id="sender_notify",
        )
        self.chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
            assigned_to=self.manager,
        )
        InstagramConnection.objects.create(
            shop=self.shop,
            instagram_user_id="shop_ig",
            page_id="page_1",
            encrypted_access_token="mock_token_test",
            instagram_username="shop",
        )
        self.api = APIClient()
        self.now = timezone.now()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_inbound_message_creates_notification(self):
        inbound = InboundInstagramMessage(
            event_id="evt-notify",
            shop_instagram_id="shop_ig",
            sender_id="sender_notify",
            recipient_id="page_1",
            message_id="msg-notify",
            text="Need help",
            timestamp_ms=int(self.now.timestamp() * 1000),
            sender_username="notify_client",
        )
        ingest_inbound_message(inbound, store_event=False)

        notifications = ChatNotification.objects.filter(
            chat=self.chat,
            kind=ChatNotification.Kind.NEW_MESSAGE,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().user_id, self.manager.id)

    def test_waiting_reply_reminder_created(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Still waiting",
            sent_at=self.now - timedelta(hours=2),
        )
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.OUTBOUND,
            content="Hi",
            sent_at=self.now - timedelta(hours=3),
        )
        self.chat.priority = Chat.Priority.WAITING_REPLY
        self.chat.save(update_fields=["priority"])

        created = send_waiting_reply_reminders(shop=self.shop, now=self.now)
        self.assertEqual(created, 1)
        notification = ChatNotification.objects.get(
            chat=self.chat,
            kind=ChatNotification.Kind.WAITING_REPLY_REMINDER,
        )
        self.assertEqual(notification.user_id, self.manager.id)

    def test_mark_notification_read(self):
        notification = ChatNotification.objects.create(
            shop=self.shop,
            chat=self.chat,
            user=self.manager,
            kind=ChatNotification.Kind.NEW_MESSAGE,
            message="New message",
        )
        self._auth(self.manager)
        response = self.api.post(f"/api/notifications/{notification.id}/read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_list_notifications_includes_unread_count(self):
        ChatNotification.objects.create(
            shop=self.shop,
            chat=self.chat,
            user=self.manager,
            kind=ChatNotification.Kind.NEW_MESSAGE,
            message="One",
        )
        ChatNotification.objects.create(
            shop=self.shop,
            chat=self.chat,
            user=self.manager,
            kind=ChatNotification.Kind.WAITING_REPLY_REMINDER,
            message="Two",
            is_read=True,
        )
        self._auth(self.manager)
        response = self.api.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["results"]), 2)

    def test_mark_all_notifications_read(self):
        ChatNotification.objects.create(
            shop=self.shop,
            chat=self.chat,
            user=self.manager,
            kind=ChatNotification.Kind.NEW_MESSAGE,
            message="One",
        )
        self._auth(self.manager)
        response = self.api.post("/api/notifications/read-all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["marked_read"], 1)
        self.assertEqual(
            ChatNotification.objects.filter(user=self.manager, is_read=False).count(),
            0,
        )
