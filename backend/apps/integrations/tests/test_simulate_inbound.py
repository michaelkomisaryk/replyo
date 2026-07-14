from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.integrations.instagram_oauth import connect_mock_account
from apps.messages.models import Chat, Message


@override_settings(DEBUG=True, META_APP_ID="", META_APP_SECRET="")
class SimulateInstagramInboundCommandTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Jojo")
        self.admin = User.objects.create_user(
            username="admin@jojo.com",
            email="admin@jojo.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        connect_mock_account(shop=self.shop, connected_by=self.admin)

    def test_simulate_creates_client_with_requested_username(self):
        call_command(
            "simulate_instagram_inbound",
            username="beauty_buyer",
            text="Do you have this in blue?",
        )

        client = Client.objects.get()
        self.assertEqual(client.instagram_username, "beauty_buyer")
        self.assertEqual(Chat.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.get().content, "Do you have this in blue?")

    def test_requires_connection(self):
        Message.objects.all().delete()
        Chat.objects.all().delete()
        Client.objects.all().delete()
        self.shop.instagram_connection.delete()

        with self.assertRaises(CommandError):
            call_command("simulate_instagram_inbound", username="orphan_user")
