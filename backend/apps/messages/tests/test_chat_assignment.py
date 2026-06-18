from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.test import TestCase

from apps.accounts.models import Shop, User, UserRole
from apps.clients.models import Client
from apps.messages.models import Chat, ChatNotification, Message, MessageDirection
from django.utils import timezone


class ChatAssignmentTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Assign Shop")
        self.admin = User.objects.create_user(
            username="admin@assign.com",
            email="admin@assign.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@assign.com",
            email="manager@assign.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.support = User.objects.create_user(
            username="support@assign.com",
            email="support@assign.com",
            password="password123",
            shop=self.shop,
            role=UserRole.SUPPORT_MANAGER,
        )
        self.client_record = Client.objects.create(
            shop=self.shop,
            instagram_username="assign_client",
            display_name="Assign Client",
        )
        self.chat = Chat.objects.create(
            shop=self.shop,
            client=self.client_record,
        )
        self.api = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_admin_can_assign_chat(self):
        self._auth(self.admin)
        response = self.api.post(
            f"/api/chats/{self.chat.id}/assign/",
            {"assigned_to": self.support.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["assigned_to"], self.support.id)
        self.assertEqual(response.data["assigned_to_email"], self.support.email)

    def test_manager_can_list_team_members(self):
        self._auth(self.manager)
        response = self.api.get("/api/users/?team=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {user["email"] for user in response.data}
        self.assertIn(self.support.email, emails)

    def test_support_manager_can_escalate_assigned_chat(self):
        self.chat.assigned_to = self.support
        self.chat.save(update_fields=["assigned_to"])

        self._auth(self.support)
        response = self.api.post(f"/api/chats/{self.chat.id}/escalate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["assigned_to"])

    def test_support_manager_cannot_escalate_unassigned_chat(self):
        self._auth(self.support)
        response = self.api.post(f"/api/chats/{self.chat.id}/escalate/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_chats_by_assignee(self):
        assigned = Chat.objects.create(
            shop=self.shop,
            client=Client.objects.create(
                shop=self.shop,
                instagram_username="assigned_one",
                display_name="Assigned One",
            ),
            assigned_to=self.support,
        )
        Chat.objects.create(
            shop=self.shop,
            client=Client.objects.create(
                shop=self.shop,
                instagram_username="unassigned_one",
                display_name="Unassigned One",
            ),
        )

        self._auth(self.admin)
        response = self.api.get(f"/api/chats/?view=all&assigned_to={self.support.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {chat["id"] for chat in response.data}
        self.assertEqual(ids, {assigned.id})

    def test_priorities_endpoint_filters_by_assignee(self):
        self.chat.assigned_to = self.manager
        self.chat.save(update_fields=["assigned_to"])
        Message.objects.create(
            chat=self.chat,
            direction=MessageDirection.INBOUND,
            content="hello",
            sent_at=timezone.now(),
        )

        self._auth(self.admin)
        response = self.api.get(f"/api/chats/priorities/?assigned_to={self.manager.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chat_ids = {
            chat["id"]
            for bucket in response.data["buckets"]
            for chat in bucket["chats"]
        }
        self.assertEqual(chat_ids, {self.chat.id})

    def test_escalate_notifies_managers(self):
        self.chat.assigned_to = self.support
        self.chat.save(update_fields=["assigned_to"])

        self._auth(self.support)
        response = self.api.post(f"/api/chats/{self.chat.id}/escalate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notifications = ChatNotification.objects.filter(
            chat=self.chat,
            kind=ChatNotification.Kind.CHAT_ESCALATED,
        )
        self.assertEqual(notifications.count(), 2)
        recipients = {notification.user_id for notification in notifications}
        self.assertEqual(recipients, {self.admin.id, self.manager.id})

    def test_support_manager_only_sees_assigned_chats_in_list(self):
        assigned = Chat.objects.create(
            shop=self.shop,
            client=Client.objects.create(
                shop=self.shop,
                instagram_username="support_chat",
                display_name="Support Chat",
            ),
            assigned_to=self.support,
        )
        Chat.objects.create(
            shop=self.shop,
            client=Client.objects.create(
                shop=self.shop,
                instagram_username="other_chat",
                display_name="Other Chat",
            ),
            assigned_to=self.manager,
        )

        self._auth(self.support)
        response = self.api.get("/api/chats/?view=all")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {chat["id"] for chat in response.data}
        self.assertEqual(ids, {assigned.id})
