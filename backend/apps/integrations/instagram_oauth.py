from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone

from apps.integrations.models import InstagramConnection
from apps.integrations.token_store import decrypt_token, encrypt_token

STATE_SALT = "instagram-oauth-state"
GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
OAUTH_SCOPES = ",".join(
    [
        "instagram_basic",
        "instagram_manage_messages",
        "pages_show_list",
        "pages_read_engagement"
    ]
)


@dataclass
class InstagramAccountInfo:
    instagram_user_id: str
    instagram_username: str
    page_id: str
    access_token: str


class InstagramOAuthError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def is_oauth_configured() -> bool:
    return bool(settings.META_APP_ID and settings.META_APP_SECRET)


def mock_oauth_enabled() -> bool:
    return settings.DEBUG and not is_oauth_configured()


def build_oauth_state(*, shop_id: int, user_id: int) -> str:
    return signing.dumps(
        {"shop_id": shop_id, "user_id": user_id},
        salt=STATE_SALT,
    )


def parse_oauth_state(state: str) -> dict:
    return signing.loads(state, salt=STATE_SALT, max_age=600)


def build_authorization_url(*, shop_id: int, user_id: int) -> str:
    if not is_oauth_configured():
        raise InstagramOAuthError("Meta OAuth is not configured.")

    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "state": build_oauth_state(shop_id=shop_id, user_id=user_id),
        "scope": OAUTH_SCOPES,
        "response_type": "code",
    }
    query = urllib.parse.urlencode(params)
    return f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?{query}"


def _http_get(url: str, params: dict | None = None) -> dict:
    if params:
        query = urllib.parse.urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    request = urllib.request.Request(url, headers={"User-Agent": "replyo-integrations"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            payload = json.loads(body)
            message = payload.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            message = body or str(exc)
        raise InstagramOAuthError(message) from exc
    except urllib.error.URLError as exc:
        raise InstagramOAuthError(str(exc)) from exc


def _exchange_code_for_token(code: str) -> tuple[str, int | None]:
    payload = _http_get(
        f"{GRAPH_BASE_URL}/oauth/access_token",
        {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": settings.META_REDIRECT_URI,
            "code": code,
        },
    )
    access_token = payload.get("access_token")
    if not access_token:
        raise InstagramOAuthError("Meta did not return an access token.")
    expires_in = payload.get("expires_in")
    return access_token, int(expires_in) if expires_in is not None else None


def _exchange_for_long_lived_token(short_lived_token: str) -> tuple[str, int | None]:
    payload = _http_get(
        f"{GRAPH_BASE_URL}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_lived_token,
        },
    )
    access_token = payload.get("access_token")
    if not access_token:
        raise InstagramOAuthError("Meta did not return a long-lived access token.")
    expires_in = payload.get("expires_in")
    return access_token, int(expires_in) if expires_in is not None else None


def _fetch_instagram_account(access_token: str) -> InstagramAccountInfo:
    payload = _http_get(
        f"{GRAPH_BASE_URL}/me/accounts",
        {
            "fields": "id,access_token,instagram_business_account{id,username}",
            "access_token": access_token,
        },
    )
    pages = payload.get("data", [])
    for page in pages:
        instagram_account = page.get("instagram_business_account")
        if not instagram_account:
            continue
        page_access_token = page.get("access_token") or access_token
        username = instagram_account.get("username") or instagram_account.get("id", "")
        return InstagramAccountInfo(
            instagram_user_id=str(instagram_account["id"]),
            instagram_username=username,
            page_id=str(page.get("id", "")),
            access_token=page_access_token,
        )

    raise InstagramOAuthError(
        "No Instagram business account was found for this Facebook login."
    )


def _expires_at(expires_in: int | None):
    if expires_in is None:
        return None
    return timezone.now() + timedelta(seconds=expires_in)


def save_connection(
    *,
    shop,
    connected_by,
    account: InstagramAccountInfo,
    expires_in: int | None,
) -> InstagramConnection:
    onboarding_settings = shop.settings.get("onboarding", {})
    onboarding_settings["instagram_connected"] = True
    shop.settings["onboarding"] = onboarding_settings
    shop.save(update_fields=["settings", "updated_at"])

    connection, _created = InstagramConnection.objects.update_or_create(
        shop=shop,
        defaults={
            "instagram_user_id": account.instagram_user_id,
            "instagram_username": account.instagram_username,
            "page_id": account.page_id,
            "encrypted_access_token": encrypt_token(account.access_token),
            "token_expires_at": _expires_at(expires_in),
            "connected_by": connected_by,
        },
    )
    return connection


def connect_with_authorization_code(
    *,
    shop,
    connected_by,
    code: str,
) -> InstagramConnection:
    short_lived_token, _short_expiry = _exchange_code_for_token(code)
    long_lived_token, long_expiry = _exchange_for_long_lived_token(short_lived_token)
    account = _fetch_instagram_account(long_lived_token)
    return save_connection(
        shop=shop,
        connected_by=connected_by,
        account=account,
        expires_in=long_expiry,
    )


def connect_mock_account(*, shop, connected_by) -> InstagramConnection:
    slug = shop.name.lower().replace(" ", "_")[:24] or "shop"
    account = InstagramAccountInfo(
        instagram_user_id=f"mock_{shop.id}",
        instagram_username=f"{slug}_ig",
        page_id=f"mock_page_{shop.id}",
        access_token=f"mock_token_{shop.id}",
    )
    return save_connection(
        shop=shop,
        connected_by=connected_by,
        account=account,
        expires_in=60 * 60 * 24 * 60,
    )


def refresh_connection_token(connection: InstagramConnection) -> InstagramConnection:
    current_token = decrypt_token(connection.encrypted_access_token)
    if current_token.startswith("mock_token_"):
        connection.token_expires_at = _expires_at(60 * 60 * 24 * 60)
        connection.save(update_fields=["token_expires_at", "updated_at"])
        return connection

    if not is_oauth_configured():
        raise InstagramOAuthError("Meta OAuth is not configured.")

    refreshed_token, expires_in = _exchange_for_long_lived_token(current_token)
    connection.encrypted_access_token = encrypt_token(refreshed_token)
    connection.token_expires_at = _expires_at(expires_in)
    connection.save(
        update_fields=["encrypted_access_token", "token_expires_at", "updated_at"]
    )
    return connection


def disconnect_instagram(*, shop) -> None:
    InstagramConnection.objects.filter(shop=shop).delete()
    onboarding_settings = shop.settings.get("onboarding", {})
    onboarding_settings["instagram_connected"] = False
    shop.settings["onboarding"] = onboarding_settings
    shop.save(update_fields=["settings", "updated_at"])


def get_connection_status(*, shop, can_manage: bool) -> dict:
    try:
        connection = shop.instagram_connection
    except InstagramConnection.DoesNotExist:
        return {
            "connected": False,
            "username": None,
            "instagram_user_id": None,
            "connected_at": None,
            "token_expires_at": None,
            "can_manage": can_manage,
            "oauth_configured": is_oauth_configured(),
            "mock_available": mock_oauth_enabled(),
        }

    return {
        "connected": True,
        "username": connection.instagram_username,
        "instagram_user_id": connection.instagram_user_id,
        "connected_at": connection.created_at.isoformat(),
        "token_expires_at": (
            connection.token_expires_at.isoformat()
            if connection.token_expires_at
            else None
        ),
        "can_manage": can_manage,
        "oauth_configured": is_oauth_configured(),
        "mock_available": mock_oauth_enabled(),
    }
