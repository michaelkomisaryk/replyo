#!/usr/bin/env python3
"""Update GitHub issue #9: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 9

UPDATED_BODY = """## Summary

Allow team members to reply to clients directly from MicroCRM.

## Tasks

- [x] Send message API via Meta Graph API
- [x] Store outbound messages in Message model
- [x] Reply composer UI in chat detail view
- [x] Handle API errors and rate limits gracefully
- [x] Show send status (sending, sent, failed)

## Acceptance criteria

- [x] Team member can send a reply from chat UI
- [x] Reply is delivered to Instagram and stored in CRM
- [x] Failed sends show actionable error to user

## References

- `docs/user-flows.md` — Seller Flow
"""

COMMENT = """## Completed

Send Instagram DM replies from CRM is implemented on `main`.

### Backend
- `POST /api/chats/<id>/reply/` — send reply via Meta Graph API (mock in dev)
- Outbound messages stored with `delivery_status` (`sending`, `sent`, `failed`) and `delivery_error`
- Rate limits and Graph API errors return actionable messages (HTTP 429 when retryable)
- `GET /api/messages/?chat=<id>` — filter messages for chat detail view
- Chat serializer includes client username/display name for UI

### Frontend
- `/chats` — chat list page
- `/chats/[id]` — message thread with inbound/outbound styling
- `ReplyComposer` with sending/sent/failed status feedback
- Delivery status shown on outbound messages in thread

### Verified
- 7 outbound reply API tests pass
- `npm run build` succeeds with `/chats` routes
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
            "User-Agent": "replyo-update-issue-9",
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
