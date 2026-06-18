from __future__ import annotations

import json
import uuid
import urllib.error
import urllib.request

from django.utils import timezone

from apps.integrations.instagram_oauth import GRAPH_BASE_URL
from apps.integrations.models import InstagramConnection
from apps.integrations.token_store import decrypt_token
from apps.messages.models import (
    Chat,
    Message,
    MessageDeliveryStatus,
    MessageDirection,
)


class OutboundSendError(Exception):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(message)


def _parse_graph_error(body: str, status_code: int) -> OutboundSendError:
    try:
        payload = json.loads(body)
        message = payload.get("error", {}).get("message", body)
        error_code = payload.get("error", {}).get("code")
    except json.JSONDecodeError:
        message = body or "Instagram API request failed."
        error_code = None

    retryable = status_code == 429 or error_code in {4, 17, 32, 613}
    if status_code == 429:
        message = "Instagram rate limit reached. Please wait and try again."

    return OutboundSendError(message, retryable=retryable, status_code=status_code)


def send_instagram_text_message(
    *,
    connection: InstagramConnection,
    recipient_id: str,
    text: str,
) -> str:
    token = decrypt_token(connection.encrypted_access_token)
    if token.startswith("mock_token_"):
        return f"mock_mid_{uuid.uuid4().hex}"

    payload = json.dumps(
        {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
    ).encode("utf-8")
    url = f"{GRAPH_BASE_URL}/{connection.instagram_user_id}/messages"
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "replyo-integrations",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise _parse_graph_error(exc.read().decode(), exc.code) from exc
    except urllib.error.URLError as exc:
        raise OutboundSendError(
            "Could not reach Instagram. Check your connection and try again.",
            retryable=True,
        ) from exc

    message_id = result.get("message_id") or result.get("id")
    if not message_id:
        raise OutboundSendError("Instagram did not return a message ID.")
    return str(message_id)


def get_shop_instagram_connection(shop) -> InstagramConnection:
    try:
        return shop.instagram_connection
    except InstagramConnection.DoesNotExist as exc:
        raise OutboundSendError(
            "Instagram is not connected for this shop. Connect it in Settings."
        ) from exc


def send_chat_reply(*, chat: Chat, content: str) -> Message:
    content = content.strip()
    if not content:
        raise OutboundSendError("Message cannot be empty.")

    client = chat.client
    if not client.instagram_user_id:
        raise OutboundSendError(
            "This client has no Instagram user ID yet. Wait for an inbound message first."
        )

    connection = get_shop_instagram_connection(chat.shop)
    message = Message.objects.create(
        chat=chat,
        direction=MessageDirection.OUTBOUND,
        content=content,
        sent_at=timezone.now(),
        delivery_status=MessageDeliveryStatus.SENDING,
    )
    chat.save(update_fields=["updated_at"])

    try:
        external_id = send_instagram_text_message(
            connection=connection,
            recipient_id=client.instagram_user_id,
            text=content,
        )
    except OutboundSendError as exc:
        message.delivery_status = MessageDeliveryStatus.FAILED
        message.delivery_error = exc.message
        message.save(update_fields=["delivery_status", "delivery_error", "updated_at"])
        raise

    message.external_id = external_id
    message.delivery_status = MessageDeliveryStatus.SENT
    message.delivery_error = ""
    message.save(
        update_fields=[
            "external_id",
            "delivery_status",
            "delivery_error",
            "updated_at",
        ]
    )

    from apps.messages.priority import recalculate_chat_priority

    recalculate_chat_priority(chat)
    return message
