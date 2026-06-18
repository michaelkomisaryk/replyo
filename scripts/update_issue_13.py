#!/usr/bin/env python3
"""Update GitHub issue #13: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 13

UPDATED_BODY = """## Summary

Control which chats appear on the dashboard per `docs/smart-chat-visibility.md`.

## Tasks

- [x] Active/inactive chat logic (7-day window, open orders, pinned)
- [x] Auto-archive completed orders after 24 hours
- [x] Hide rejected clients from main view by default
- [x] Auto-reactivate archived chat on new inbound message
- [x] Archive search API

## Acceptance criteria

- [x] Inactive chats hidden from main dashboard
- [x] Completed order chats archive after 24 hours
- [x] New message from archived client reactivates chat and triggers notification
"""

COMMENT = """## Completed

Smart chat visibility and auto-archiving (backend) is implemented on `main`.

### Backend
- `apps/messages/visibility.py` — active/inactive rules (7-day window, open orders, pinned, completed 24h window)
- Chat fields: `is_pinned`, `is_archived`, `archived_at`, `has_new_message_badge`
- Order `completed_at` timestamp set when status becomes Completed
- `GET /api/chats/` defaults to `view=active` (hides inactive and rejected chats)
- `GET /api/chats/?view=archived|rejected|all` — alternate views
- `GET /api/chats/archive/search/?q=` — search archived chats by client name/username
- `POST /api/chats/<id>/pin/` and `POST /api/chats/<id>/archive/` — manager/admin actions
- `GET /api/notifications/` — reactivation notifications for assigned manager or admins
- Inbound Instagram messages auto-reactivate archived chats and create notifications
- `python3 backend/manage.py archive_inactive_chats` — scheduled auto-archive job
- `CHAT_ACTIVE_MESSAGE_WINDOW_DAYS` and `CHAT_COMPLETED_VISIBLE_HOURS` env settings

### Verified
- 14 chat visibility tests pass
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
            "User-Agent": "replyo-update-issue-13",
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
