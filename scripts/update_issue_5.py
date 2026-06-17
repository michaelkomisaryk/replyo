#!/usr/bin/env python3
"""Update GitHub issue #5: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 5

UPDATED_BODY = """## Summary

Implement role-based access per `docs/user-roles.md`.

## Roles

- **Admin** — full access
- **Manager** — chats, orders, client cards
- **Support Manager** — assigned chats only, read-only client cards

## Tasks

- [x] Role field on User model
- [x] DRF permission classes per role
- [x] Enforce permissions on chat, order, and client endpoints
- [x] Permission summary covered by API tests

## Acceptance criteria

- [x] Admin can access all resources
- [x] Support Manager cannot update orders or edit client cards
- [x] Support Manager only sees assigned chats
"""

COMMENT = """## Completed

Role-based permissions are implemented on `main`.

### Backend
- Reused existing `User.role` field (`admin`, `manager`, `support_manager`)
- Added DRF permission classes in `apps/common/permissions.py`
- Shop-scoped querysets with chat filtering for Support Managers
- Enforced permissions on client, chat, and order endpoints
- Client/order writes restricted to Admin and Manager
- Support Managers can read client cards but cannot update them or orders

### Tests
- `apps/accounts/tests/test_role_permissions.py` — 9 API tests covering the permission matrix

### Verified
- Admin can access all shop chats and orders
- Support Manager only sees assigned chats
- Support Manager cannot PATCH clients or orders
- Manager can update clients and orders
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
            "User-Agent": "replyo-update-issue-5",
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
