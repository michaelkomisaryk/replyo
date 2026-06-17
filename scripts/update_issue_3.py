#!/usr/bin/env python3
"""Update GitHub issue #3: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 3

UPDATED_BODY = """## Summary

Design and implement core Django models for the MVP domain.

## Models

- **Shop** — business account (name, settings)
- **User** — team member linked to shop with role
- **Client** — Instagram customer (username, display name, notes)
- **Chat** — conversation thread linked to client
- **Message** — individual message (inbound/outbound, timestamps)
- **Order** — order linked to client/chat with status

## Order statuses

`New Client`, `Waiting Payment`, `Paid`, `Sent`, `Completed`, `Rejected`

## Acceptance criteria

- [x] Models and migrations created for all entities
- [x] Foreign keys and indexes defined for common queries
- [x] Django admin registered for debugging
- [x] Basic serializers expose read endpoints
"""

COMMENT = """## Completed

Core database models are implemented on `main`.

### Models
- `Shop`, `User` (custom auth user with role) in `apps.accounts`
- `Client` in `apps.clients`
- `Chat`, `Message` in `apps.messages` (app label `crm_messages`)
- `Order` with status workflow in `apps.orders`

### Order statuses
`new_client`, `waiting_payment`, `paid`, `sent`, `completed`, `rejected`

### API read endpoints
- `GET /api/shops/`
- `GET /api/users/`
- `GET /api/clients/`
- `GET /api/chats/`
- `GET /api/messages/`
- `GET /api/orders/`

### Also delivered
- Initial migrations for all apps
- Indexes on common query fields (shop + username, shop + status, chat + sent_at, etc.)
- Django admin registration for all models
- DRF read-only viewsets and serializers

### Verified
- `python backend/manage.py makemigrations` / `migrate` — success
- `python backend/manage.py check` — no issues
- All list endpoints return HTTP 200 with JSON payloads
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
            "User-Agent": "replyo-update-issue-3",
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
