#!/usr/bin/env python3
"""Update GitHub issue #14: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 14

UPDATED_BODY = """## Summary

Build the main dashboard view per MVP scope.

## Tasks

- [x] Chat list grouped by priority buckets
- [x] Show wait time and urgency indicators
- [x] New clients and waiting-for-reply sections at top
- [x] Filter tabs (all, active orders, archived, rejected)
- [x] Empty states and loading skeletons
- [x] Responsive layout for desktop

## Acceptance criteria

- [x] Dashboard shows chats in priority order
- [x] Wait time visible for Waiting for Reply chats
- [x] User can switch between main filters
"""

COMMENT = """## Completed

Dashboard UI with prioritized chat list is implemented on `main`.

### Frontend
- `ChatDashboard` — main prioritized inbox on `/chats`
- Priority buckets from `GET /api/chats/priorities/` (New Clients and Waiting for Reply at top)
- `ChatRow` — wait time badges with yellow/orange/red urgency for Waiting for Reply chats
- Filter tabs: All, Active orders, Archived, Rejected (wired to backend `view` / `priority` params)
- Loading skeletons (`ChatDashboardSkeleton`) and per-filter empty states
- Responsive layout with `max-w-5xl` content area inside the desktop shell
- Extended `Chat` API types and `fetchChatPriorities()` helper

### Verified
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
            "User-Agent": "replyo-update-issue-14",
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
