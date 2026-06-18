import json

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole


class OnboardingInvitationTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Onboarding Shop")
        self.admin = User.objects.create_user(
            username="admin@shop.com",
            email="admin@shop.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
            is_email_verified=False,
        )
        self.client = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_new_admin_sees_onboarding_checklist(self):
        self._auth(self.admin)
        response = self.client.get("/api/onboarding/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["completed_count"], 0)
        self.assertFalse(payload["is_complete"])
        step_ids = {step["id"] for step in payload["steps"]}
        self.assertEqual(
            step_ids,
            {"email_verified", "instagram_connected", "team_invited"},
        )

    def test_checklist_marks_email_verified_step_complete(self):
        self.admin.is_email_verified = True
        self.admin.save(update_fields=["is_email_verified"])
        self._auth(self.admin)
        response = self.client.get("/api/onboarding/")
        email_step = next(
            step for step in response.json()["steps"] if step["id"] == "email_verified"
        )
        self.assertTrue(email_step["completed"])

    def test_admin_can_invite_team_member(self):
        mail.outbox.clear()
        self._auth(self.admin)
        response = self.client.post(
            "/api/invitations/",
            {"email": "manager@shop.com", "role": UserRole.MANAGER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("manager@shop.com", mail.outbox[0].to)

    def test_invited_member_can_accept_and_log_in(self):
        self._auth(self.admin)
        invite_response = self.client.post(
            "/api/invitations/",
            {"email": "support@shop.com", "role": UserRole.SUPPORT_MANAGER},
            format="json",
        )
        token = invite_response.json()["token"] if "token" in invite_response.json() else None
        if not token:
            from apps.accounts.invitations import TeamInvitation

            invitation = TeamInvitation.objects.get(email="support@shop.com")
            token = str(invitation.token)

        self.client.credentials()
        accept_response = self.client.post(
            "/api/invitations/accept/",
            {"token": token, "password": "newpassword123"},
            format="json",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="support@shop.com").exists())

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "support@shop.com", "password": "newpassword123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    @override_settings(DEBUG=True, META_APP_ID="", META_APP_SECRET="")
    def test_checklist_tracks_team_invite_completion(self):
        self.admin.is_email_verified = True
        self.admin.save(update_fields=["is_email_verified"])
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        self.client.post(
            "/api/invitations/",
            {"email": "manager@shop.com", "role": UserRole.MANAGER},
            format="json",
        )
        response = self.client.get("/api/onboarding/")
        team_step = next(
            step for step in response.json()["steps"] if step["id"] == "team_invited"
        )
        self.assertTrue(team_step["completed"])
        self.assertTrue(response.json()["is_complete"])
