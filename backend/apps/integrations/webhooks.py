from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone

from django.conf import settings


@dataclass
class InboundInstagramMessage:
    event_id: str
    shop_instagram_id: str
    sender_id: str
    recipient_id: str
    message_id: str
    text: str
    timestamp_ms: int
    sender_username: str = ""


def verify_webhook_signature(payload: bytes, signature_header: str | None) -> bool:
    secret = settings.META_APP_SECRET
    if not secret:
        return settings.DEBUG

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


def verify_webhook_token(token: str | None) -> bool:
    expected = settings.META_WEBHOOK_VERIFY_TOKEN
    if not expected:
        return settings.DEBUG and bool(token)
    return token == expected


def _extract_text(message: dict) -> str:
    if message.get("text"):
        return str(message["text"])
    if message.get("attachments"):
        attachment = message["attachments"][0]
        attachment_type = attachment.get("type", "attachment")
        return f"[{attachment_type}]"
    return ""


def parse_instagram_webhook(payload: dict) -> list[InboundInstagramMessage]:
    if payload.get("object") != "instagram":
        return []

    messages: list[InboundInstagramMessage] = []
    for entry in payload.get("entry", []):
        shop_instagram_id = str(entry.get("id", ""))
        for item in entry.get("messaging", []):
            message = item.get("message")
            if not message or message.get("is_echo"):
                continue

            message_id = str(message.get("mid", ""))
            if not message_id:
                continue

            sender = item.get("sender", {})
            recipient = item.get("recipient", {})
            sender_id = str(sender.get("id", ""))
            recipient_id = str(recipient.get("id", ""))
            if not sender_id or not recipient_id:
                continue

            timestamp_ms = int(item.get("timestamp", 0))
            sender_username = str(sender.get("username", "") or "")
            event_id = f"{message_id}:{timestamp_ms}"

            messages.append(
                InboundInstagramMessage(
                    event_id=event_id,
                    shop_instagram_id=shop_instagram_id,
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    message_id=message_id,
                    text=_extract_text(message),
                    timestamp_ms=timestamp_ms,
                    sender_username=sender_username,
                )
            )

    return messages


def webhook_payload_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def timestamp_to_datetime(timestamp_ms: int) -> datetime:
    if timestamp_ms <= 0:
        return datetime.now(tz=dt_timezone.utc)
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=dt_timezone.utc)


def build_mock_webhook_payload(
    *,
    shop_instagram_id: str,
    sender_id: str,
    recipient_id: str,
    message_id: str,
    text: str,
    timestamp_ms: int | None = None,
    sender_username: str = "",
) -> dict:
    timestamp = timestamp_ms or int(datetime.now(tz=dt_timezone.utc).timestamp() * 1000)
    sender = {"id": sender_id}
    if sender_username:
        sender["username"] = sender_username

    return {
        "object": "instagram",
        "entry": [
            {
                "id": shop_instagram_id,
                "time": timestamp,
                "messaging": [
                    {
                        "sender": sender,
                        "recipient": {"id": recipient_id},
                        "timestamp": timestamp,
                        "message": {
                            "mid": message_id,
                            "text": text,
                        },
                    }
                ],
            }
        ],
    }


def dumps_payload(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")
