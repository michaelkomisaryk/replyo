#!/usr/bin/env python3
"""Update GitHub issue #15: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 15

UPDATED_BODY = """## Summary

Build the conversation view for reading and replying to messages.

## Tasks

- [x] Message thread UI (inbound/outbound styling)
- [x] Reply composer with send button
- [x] Client card sidebar/panel
- [x] Order status widget
- [x] Assignment and status controls
- [x] Real-time or polling refresh for new messages

## Acceptance criteria

- [x] Full message history visible in chat view
- [x] User can compose and send reply
- [x] Client card and order status visible alongside chat
"""

COMMENT = """## Completed

Chat detail view with reply composer is implemented on `main`.

### Frontend
- `MessageThread` — inbound/outbound bubbles with labels, delivery status, auto-scroll
- `ReplyComposer` — send via Instagram with retry feedback
- Right sidebar: `ChatControls`, `OrderStatusPanel`, `ClientCardPanel`
- `ChatControls` — assign team member, pin/archive, escalate (support), priority + wait time
- `ChatDetailSkeleton` loading state
- Polling refresh: messages every 5s, chat metadata every 10s

### Backend (supporting assignment controls)
- `POST /api/chats/<id>/assign/` — admin/manager assign or unassign
- `POST /api/chats/<id>/escalate/` — support manager escalates to team
- `GET /api/users/?team=1` — team list for assign dropdown (manager)
- Chat API includes `assigned_to_email`

### Verified
- 4 chat assignment API tests pass
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
            "User-Agent": "replyo-update-issue-15",
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
