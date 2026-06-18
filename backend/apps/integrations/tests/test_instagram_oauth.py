import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Shop, User, UserRole
from apps.integrations.models import InstagramConnection


@override_settings(DEBUG=True, META_APP_ID="", META_APP_SECRET="")
class InstagramIntegrationTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="IG Shop")
        self.admin = User.objects.create_user(
            username="admin@igshop.com",
            email="admin@igshop.com",
            password="password123",
            shop=self.shop,
            role=UserRole.ADMIN,
        )
        self.manager = User.objects.create_user(
            username="manager@igshop.com",
            email="manager@igshop.com",
            password="password123",
            shop=self.shop,
            role=UserRole.MANAGER,
        )
        self.client = APIClient()

    def _auth(self, user: User) -> None:
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_status_not_connected(self):
        self._auth(self.admin)
        response = self.client.get("/api/integrations/instagram/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertFalse(payload["connected"])
        self.assertTrue(payload["can_manage"])
        self.assertTrue(payload["mock_available"])

    def test_admin_can_mock_connect(self):
        self._auth(self.admin)
        response = self.client.post("/api/integrations/instagram/mock-connect/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["connected"])
        self.assertEqual(payload["username"], "ig_shop_ig")
        self.assertTrue(
            InstagramConnection.objects.filter(shop=self.shop).exists()
        )

    def test_manager_cannot_mock_connect(self):
        self._auth(self.manager)
        response = self.client.post("/api/integrations/instagram/mock-connect/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_view_status_but_not_manage(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        self._auth(self.manager)
        response = self.client.get("/api/integrations/instagram/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["connected"])
        self.assertFalse(payload["can_manage"])

    def test_admin_can_disconnect(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        response = self.client.post("/api/integrations/instagram/disconnect/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            InstagramConnection.objects.filter(shop=self.shop).exists()
        )

    def test_manager_cannot_disconnect(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        self._auth(self.manager)
        response = self.client.post("/api/integrations/instagram/disconnect/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_refresh_mock_token(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        response = self.client.post("/api/integrations/instagram/refresh/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["connected"])

    @override_settings(
        META_APP_ID="test-app-id",
        META_APP_SECRET="test-app-secret",
        META_REDIRECT_URI="http://127.0.0.1:8000/api/integrations/instagram/callback/",
    )
    def test_connect_returns_authorization_url(self):
        self._auth(self.admin)
        response = self.client.get("/api/integrations/instagram/connect/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("facebook.com", payload["authorization_url"])
        self.assertFalse(payload["mock_available"])

    @override_settings(
        META_APP_ID="test-app-id",
        META_APP_SECRET="test-app-secret",
        META_REDIRECT_URI="http://127.0.0.1:8000/api/integrations/instagram/callback/",
    )
    @patch("apps.integrations.views.connect_with_authorization_code")
    def test_oauth_callback_redirects_to_settings(self, mock_connect):
        mock_connect.return_value = InstagramConnection(
            shop=self.shop,
            instagram_user_id="123",
            instagram_username="shop_ig",
            encrypted_access_token="encrypted",
        )
        state = json.dumps({"shop_id": self.shop.id, "user_id": self.admin.id})
        with patch(
            "apps.integrations.views.parse_oauth_state",
            return_value={"shop_id": self.shop.id, "user_id": self.admin.id},
        ):
            response = self.client.get(
                "/api/integrations/instagram/callback/",
                {"code": "test-code", "state": state},
            )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/settings?instagram=connected", response["Location"])
        mock_connect.assert_called_once()

    def test_onboarding_marks_instagram_complete_after_connect(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        response = self.client.get("/api/onboarding/")
        instagram_step = next(
            step
            for step in response.json()["steps"]
            if step["id"] == "instagram_connected"
        )
        self.assertTrue(instagram_step["completed"])
        self.assertFalse(instagram_step["placeholder"])

    def test_status_never_returns_access_token(self):
        self._auth(self.admin)
        self.client.post("/api/integrations/instagram/mock-connect/")
        response = self.client.get("/api/integrations/instagram/status/")
        payload = response.json()
        self.assertNotIn("access_token", payload)
        self.assertNotIn("encrypted_access_token", payload)
