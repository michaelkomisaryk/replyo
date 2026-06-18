#!/usr/bin/env python3
"""Update GitHub issue #12: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 12

UPDATED_BODY = """## Summary

Automatically categorize chats into priority buckets per `docs/chat-priority-system.md`.

## Priority buckets

1. **New Clients** — first message, no reply yet
2. **Waiting for Reply** — no response within time window (e.g. 1 hour)
3. **Active Orders** — confirmed order in progress
4. **Completed Orders** — delivered/closed
5. **Rejected Clients** — flagged or blocked

## Tasks

- [x] Priority calculation service
- [x] Scheduled job to recalculate wait times
- [x] API returns chats grouped or tagged by priority
- [x] Color-coded wait time metadata for Waiting for Reply

## Acceptance criteria

- [x] New unreplied chat appears in New Clients bucket
- [x] Chat moves to Waiting for Reply after threshold
- [x] Active order chat appears in Active Orders bucket
"""

COMMENT = """## Completed

Chat priority system (backend) is implemented on `main`.

### Backend
- `apps/messages/priority.py` — priority calculation from messages and orders
- `GET /api/chats/priorities/` — chats grouped into 5 priority buckets
- `GET /api/chats/?priority=<bucket>` — filter chats by priority
- Chat list/detail includes `priority_label`, `wait_seconds`, `wait_urgency` (yellow/orange/red)
- Auto-recalculate on inbound/outbound messages and order status changes
- `python3 backend/manage.py recalculate_chat_priorities` — scheduled fallback job
- `CHAT_WAITING_REPLY_THRESHOLD_SECONDS` env setting (default 1 hour)

### Verified
- 7 chat priority tests pass (13 total with order workflow regression)
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
            "User-Agent": "replyo-update-issue-12",
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
