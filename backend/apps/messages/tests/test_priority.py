from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.messages.models import Chat, Message, MessageDirection
from apps.messages.priority import (
    calculate_chat_priority,
    get_wait_urgency,
    recalculate_all_priorities,
)
from apps.orders.models import Order, OrderStatus


@override_settings(CHAT_WAITING_REPLY_THRESHOLD_SECONDS=3600)
class ChatPriorityTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Priority Shop")
        self.manager = User.objects.create_user(
            username="manager@priority.com",
            email="manager@priority.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="priority_client",
            display_name="Priority Client",
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

    def test_new_unreplied_chat_is_new_clients(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Hello",
            sent_at=self.now,
        )
        priority = calculate_chat_priority(self.chat, now=self.now)
        self.assertEqual(priority, Chat.Priority.NEW_CLIENTS)

    def test_chat_moves_to_waiting_reply_after_threshold(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="First",
            sent_at=self.now - timedelta(hours=3),
        )
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.OUTBOUND,
            content="Reply",
            sent_at=self.now - timedelta(hours=2, minutes=30),
        )
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Follow up",
            sent_at=self.now - timedelta(hours=2),
        )
        priority = calculate_chat_priority(self.chat, now=self.now)
        self.assertEqual(priority, Chat.Priority.WAITING_REPLY)

    def test_active_order_chat_is_active_orders_bucket(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Order please",
            sent_at=self.now - timedelta(hours=5),
        )
        Order.objects.create(
            shop=self.shop,
            client=self.client_record,
            chat=self.chat,
            status=OrderStatus.WAITING_PAYMENT,
        )
        priority = calculate_chat_priority(self.chat, now=self.now)
        self.assertEqual(priority, Chat.Priority.ACTIVE_ORDERS)

    def test_wait_urgency_is_color_coded(self):
        self.chat.priority = Chat.Priority.WAITING_REPLY
        self.chat.save(update_fields=["priority"])
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Waiting",
            sent_at=self.now - timedelta(hours=3),
        )
        self.assertEqual(get_wait_urgency(self.chat, now=self.now), "orange")

    def test_priorities_api_returns_grouped_buckets(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Hello",
            sent_at=self.now,
        )
        recalculate_all_priorities(now=self.now)

        self._auth(self.manager)
        response = self.api.get("/api/chats/priorities/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["wait_threshold_seconds"], 3600)
        self.assertEqual(len(payload["buckets"]), 5)

        new_clients = next(
            bucket for bucket in payload["buckets"] if bucket["priority"] == "new_clients"
        )
        self.assertEqual(new_clients["count"], 1)
        self.assertEqual(new_clients["chats"][0]["id"], self.chat.id)
        self.assertEqual(new_clients["chats"][0]["priority_label"], "New Clients")

    def test_chats_list_includes_wait_metadata(self):
        self.chat.priority = Chat.Priority.WAITING_REPLY
        self.chat.save(update_fields=["priority"])
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Waiting",
            sent_at=self.now - timedelta(hours=5),
        )

        self._auth(self.manager)
        response = self.api.get("/api/chats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chat_payload = response.json()[0]
        self.assertEqual(chat_payload["wait_urgency"], "red")
        self.assertGreaterEqual(chat_payload["wait_seconds"], 4 * 3600)

    def test_recalculate_command_updates_priorities(self):
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Hello",
            sent_at=self.now - timedelta(hours=2),
        )
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.OUTBOUND,
            content="Hi",
            sent_at=self.now - timedelta(hours=1, minutes=30),
        )
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="Any update?",
            sent_at=self.now - timedelta(hours=1, minutes=15),
        )

        from django.core.management import call_command

        call_command("recalculate_chat_priorities")
        self.chat.refresh_from_db()
        self.assertEqual(self.chat.priority, Chat.Priority.WAITING_REPLY)
