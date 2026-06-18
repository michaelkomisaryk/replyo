#!/usr/bin/env python3
"""Update GitHub issue #8: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 8

UPDATED_BODY = """## Summary

Receive Instagram DMs in real time and sync them into the CRM.

## Tasks

- [x] Register Meta webhook endpoint
- [x] Verify webhook signatures
- [x] Parse inbound DM events and create/update Chat and Message records
- [x] Link messages to existing Client by Instagram username
- [x] Background job for periodic sync fallback

## Acceptance criteria

- [x] Incoming Instagram DM creates or updates a chat in the database
- [x] Messages appear in API within seconds of webhook delivery
- [x] Duplicate events are handled idempotently

## References

- `docs/user-flows.md` — Chat Flow
- `docs/project-overview.md` — Instagram Integration
"""

COMMENT = """## Completed

Instagram webhooks and inbound message sync are implemented on `main`.

### Backend
- `GET/POST /api/integrations/instagram/webhook/` — Meta webhook verification and inbound events
- `X-Hub-Signature-256` verification using `META_APP_SECRET`
- Inbound parser creates/updates `Client`, `Chat`, and `Message` records
- Clients matched by Instagram username or `instagram_user_id`
- Idempotent ingest via unique `Message.external_id` and `InstagramWebhookEvent.event_id`
- `InstagramWebhookEvent` queue for failed/unprocessed payloads
- `python3 backend/manage.py sync_instagram_inbound` — periodic sync fallback command
- `META_WEBHOOK_VERIFY_TOKEN` env var for webhook subscription verification

### Verified
- 8 webhook/sync tests pass
- Duplicate webhook delivery does not duplicate messages
- Messages are immediately available via `GET /api/messages/`
"""


def get_token() -> str | None:
    import os

    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(key, "").strip()
        if token:
            return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def api_request(token: str, method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "replyo-update-issue-8",
        },
        method=method,
    )
    with urllib.request.urlopen(request) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def main() -> int:
    token = get_token()
    if not token:
        print("ERROR: Not authenticated. Run: gh auth login", file=sys.stderr)
        return 1

    base = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"

    api_request(token, "PATCH", base, {"body": UPDATED_BODY})
    print("Updated issue body with checked tasks.")

    api_request(token, "POST", f"{base}/comments", {"body": COMMENT})
    print("Posted completion comment.")

    api_request(token, "PATCH", base, {"state": "closed"})
    print(f"Closed issue #{ISSUE_NUMBER}.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"API error {exc.code}: {exc.read().decode()[:500]}", file=sys.stderr)
        raise SystemExit(1)
