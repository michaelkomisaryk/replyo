#!/usr/bin/env python3
"""Update GitHub issue #18: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 18

UPDATED_BODY = """## Summary

Alert team members about messages needing attention per `docs/project-overview.md`.

## Tasks

- [x] In-app notification model and API
- [x] Trigger on new inbound message
- [x] Trigger on waiting-for-reply threshold
- [x] Notification bell/dropdown in UI
- [x] Mark as read / dismiss
- [x] Notify assigned manager or admin on reactivation

## Acceptance criteria

- [x] New message creates in-app notification
- [x] Chat waiting >1 hour triggers reminder notification
- [x] User can view and dismiss notifications
"""

COMMENT = """## Completed

In-app notifications for new messages and waiting-reply reminders are implemented on `main`.

### Backend
- `ChatNotification` kinds: `new_message`, `waiting_reply_reminder`, `chat_reactivated`, `chat_escalated`
- `apps/messages/notifications.py` — centralized notification triggers
- New inbound messages notify assigned manager (or admins/managers if unassigned)
- `python3 backend/manage.py send_waiting_reply_reminders` — waiting-reply reminder job
- `GET /api/notifications/` — list with `unread_count`
- `POST /api/notifications/<id>/read/` — mark single notification read/dismissed
- `POST /api/notifications/read-all/` — dismiss all

### Frontend
- `NotificationBell` in dashboard header with unread badge
- Dropdown lists notifications, links to chat, dismiss per item or mark all read
- Polls every 30 seconds

### Verified
- 5 notification tests + existing visibility/assignment tests pass
- `npm run build` passes
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
            "User-Agent": "replyo-update-issue-18",
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
