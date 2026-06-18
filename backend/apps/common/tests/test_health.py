from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_returns_ok_with_database(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"], "ok")
