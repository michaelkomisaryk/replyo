from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from django.db import transaction
from django.utils import timezone

from apps.clients.models import Client
from apps.integrations.instagram_oauth import GRAPH_BASE_URL
from apps.integrations.models import InstagramConnection, InstagramWebhookEvent
from apps.integrations.token_store import decrypt_token
from apps.integrations.webhooks import InboundInstagramMessage, timestamp_to_datetime
from apps.messages.models import Chat, Message, MessageDirection


class InboundSyncError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def find_shop_connection(*, shop_instagram_id: str, recipient_id: str) -> InstagramConnection:
    candidates = InstagramConnection.objects.select_related("shop").filter(
        instagram_user_id=shop_instagram_id
    )
    if candidates.exists():
        return candidates.get()

    by_page = InstagramConnection.objects.select_related("shop").filter(
        page_id=recipient_id
    )
    if by_page.exists():
        return by_page.get()

    by_recipient = InstagramConnection.objects.select_related("shop").filter(
        instagram_user_id=recipient_id
    )
    if by_recipient.exists():
        return by_recipient.get()

    raise InboundSyncError(
        f"No Instagram connection found for account {shop_instagram_id}."
    )


def _normalize_username(username: str) -> str:
    return username.strip().lstrip("@").lower()


def _fetch_sender_username(connection: InstagramConnection, sender_id: str) -> str:
    token = decrypt_token(connection.encrypted_access_token)
    if token.startswith("mock_token_"):
        return ""

    params = urllib.parse.urlencode(
        {
            "fields": "username,name",
            "access_token": token,
        }
    )
    url = f"{GRAPH_BASE_URL}/{sender_id}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "replyo-integrations"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return ""

    return str(payload.get("username") or "")


def resolve_client(
    *,
    shop,
    sender_id: str,
    sender_username: str,
    connection: InstagramConnection,
) -> Client:
    if sender_username:
        normalized = _normalize_username(sender_username)
        client = Client.objects.filter(
            shop=shop,
            instagram_username__iexact=normalized,
        ).first()
        if client:
            if not client.instagram_user_id:
                client.instagram_user_id = sender_id
                client.save(update_fields=["instagram_user_id", "updated_at"])
            return client

    client = Client.objects.filter(shop=shop, instagram_user_id=sender_id).first()
    if client:
        return client

    username = sender_username.strip().lstrip("@")
    if not username:
        username = _fetch_sender_username(connection, sender_id)
    if not username:
        username = f"ig_{sender_id}"

    return Client.objects.create(
        shop=shop,
        instagram_user_id=sender_id,
        instagram_username=username,
        display_name=username,
    )


def get_or_create_chat(*, shop, client: Client) -> Chat:
    chat, _created = Chat.objects.get_or_create(shop=shop, client=client)
    return chat


@transaction.atomic
def ingest_inbound_message(
    inbound: InboundInstagramMessage,
    *,
    store_event: bool = True,
) -> Message | None:
    connection = find_shop_connection(
        shop_instagram_id=inbound.shop_instagram_id,
        recipient_id=inbound.recipient_id,
    )
    shop = connection.shop

    if store_event:
        InstagramWebhookEvent.objects.get_or_create(
            event_id=inbound.event_id,
            defaults={
                "shop": shop,
                "payload": {
                    "message_id": inbound.message_id,
                    "sender_id": inbound.sender_id,
                    "text": inbound.text,
                },
            },
        )

    existing = Message.objects.filter(external_id=inbound.message_id).first()
    if existing:
        InstagramWebhookEvent.objects.filter(event_id=inbound.event_id).update(
            processed_at=timezone.now(),
            error="",
        )
        return existing

    client = resolve_client(
        shop=shop,
        sender_id=inbound.sender_id,
        sender_username=inbound.sender_username,
        connection=connection,
    )
    chat = get_or_create_chat(shop=shop, client=client)
    message = Message.objects.create(
        chat=chat,
        direction=MessageDirection.INBOUND,
        content=inbound.text or "[empty message]",
        sent_at=timestamp_to_datetime(inbound.timestamp_ms),
        external_id=inbound.message_id,
    )
    chat.save(update_fields=["updated_at"])

    InstagramWebhookEvent.objects.filter(event_id=inbound.event_id).update(
        processed_at=timezone.now(),
        error="",
    )
    return message


def process_webhook_payload(payload: dict) -> list[Message]:
    from apps.integrations.webhooks import parse_instagram_webhook

    saved_messages: list[Message] = []
    for inbound in parse_instagram_webhook(payload):
        try:
            message = ingest_inbound_message(inbound)
        except InboundSyncError as exc:
            InstagramWebhookEvent.objects.update_or_create(
                event_id=inbound.event_id,
                defaults={
                    "payload": {
                        "message_id": inbound.message_id,
                        "sender_id": inbound.sender_id,
                        "text": inbound.text,
                    },
                    "error": exc.message,
                },
            )
            continue

        if message:
            saved_messages.append(message)

    return saved_messages


def process_unhandled_webhook_events(*, limit: int = 100) -> int:
    events = (
        InstagramWebhookEvent.objects.filter(processed_at__isnull=True)
        .order_by("created_at")[:limit]
    )

    processed_count = 0
    for event in events:
        payload = event.payload
        message_id = payload.get("message_id")
        if not message_id:
            event.error = "Missing message_id in stored payload."
            event.save(update_fields=["error", "updated_at"])
            continue

        if Message.objects.filter(external_id=message_id).exists():
            event.processed_at = timezone.now()
            event.error = ""
            event.save(update_fields=["processed_at", "error", "updated_at"])
            processed_count += 1
            continue

        if not event.shop_id:
            event.error = "Webhook event is not linked to a shop."
            event.save(update_fields=["error", "updated_at"])
            continue

        try:
            connection = InstagramConnection.objects.get(shop_id=event.shop_id)
        except InstagramConnection.DoesNotExist:
            event.error = "Shop has no Instagram connection."
            event.save(update_fields=["error", "updated_at"])
            continue

        inbound = InboundInstagramMessage(
            event_id=event.event_id,
            shop_instagram_id=connection.instagram_user_id,
            sender_id=str(payload.get("sender_id", "")),
            recipient_id=connection.page_id or connection.instagram_user_id,
            message_id=message_id,
            text=str(payload.get("text", "")),
            timestamp_ms=int(payload.get("timestamp_ms", 0)),
            sender_username=str(payload.get("sender_username", "")),
        )

        try:
            ingest_inbound_message(inbound, store_event=False)
        except InboundSyncError as exc:
            event.error = exc.message
            event.save(update_fields=["error", "updated_at"])
            continue

        processed_count += 1

    return processed_count
