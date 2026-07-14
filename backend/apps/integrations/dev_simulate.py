from __future__ import annotations

import uuid

from apps.integrations.models import InstagramConnection
from apps.integrations.webhooks import build_mock_webhook_payload
from apps.messages.models import Message


class SimulateInboundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def simulate_inbound_dm(
    *,
    username: str,
    text: str = "Hello from Instagram (dev simulation)",
    shop_id: int | None = None,
    sender_id: str | None = None,
) -> Message:
    """Inject a mock inbound Instagram DM for local development."""
    from apps.integrations.inbound_sync import process_webhook_payload

    username = username.strip().lstrip("@").lower()
    if not username:
        raise SimulateInboundError("Username is required.")

    connections = InstagramConnection.objects.select_related("shop")
    if shop_id is not None:
        connections = connections.filter(shop_id=shop_id)

    connection = connections.first()
    if not connection:
        raise SimulateInboundError(
            "No Instagram connection found. Connect your shop in Settings first."
        )

    token = connection.encrypted_access_token
    from apps.integrations.token_store import decrypt_token

    if not decrypt_token(token).startswith("mock_token_"):
        raise SimulateInboundError(
            "Simulate inbound is only available for development mock connections."
        )

    resolved_sender_id = sender_id or f"mock_sender_{username}"
    message_id = f"mock_mid_{uuid.uuid4().hex}"

    payload = build_mock_webhook_payload(
        shop_instagram_id=connection.instagram_user_id,
        sender_id=resolved_sender_id,
        recipient_id=connection.page_id or connection.instagram_user_id,
        message_id=message_id,
        text=text,
        sender_username=username,
    )

    messages = process_webhook_payload(payload)
    if not messages:
        raise SimulateInboundError("Failed to create inbound message.")

    return messages[0]
