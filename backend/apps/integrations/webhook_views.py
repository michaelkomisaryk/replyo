import json
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.inbound_sync import process_webhook_payload
from apps.integrations.webhooks import verify_webhook_signature, verify_webhook_token


@method_decorator(csrf_exempt, name="dispatch")
class InstagramWebhookView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and verify_webhook_token(token) and challenge:
            return HttpResponse(challenge, content_type="text/plain")

        return Response(
            {"detail": "Webhook verification failed."},
            status=status.HTTP_403_FORBIDDEN,
        )

    def post(self, request):
        payload_bytes = request.body
        signature = request.META.get("HTTP_X_HUB_SIGNATURE_256")

        # Перевірка підпису безпеки від Meta
        if settings.META_APP_SECRET and not verify_webhook_signature(
            payload_bytes,
            signature,
        ):
            print("❌ ПОМИЛКА: Неправильний підпис запиту (Signature) від Meta!")
            return Response(
                {"detail": "Invalid webhook signature."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Парсинг JSON-даних
        try:
            payload = request.data if isinstance(request.data, dict) else {}
            if not payload and payload_bytes:
                payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return Response(
                {"detail": "Invalid JSON payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # === ЦЕЙ ПРИНТ ОБОВ'ЯЗКОВО З'ЯВИТЬСЯ В ЛОГАХ RENDER ===
        print("🚀 УСПІХ! НАМ ПРИЛЕТІВ ВЕБХУК ВІД META:", json.dumps(payload, indent=2))

        # Передаємо повідомлення далі в твою систему синхронізації
        process_webhook_payload(payload)
        
        return Response({"status": "ok"})
