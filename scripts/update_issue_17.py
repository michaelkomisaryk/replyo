#!/usr/bin/env python3
"""Update GitHub issue #17: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 17

UPDATED_BODY = """## Summary

Search clients by name or Instagram username per MVP scope.

## Tasks

- [x] Search API with name and Instagram username
- [x] Search bar in dashboard header
- [x] Search results page or dropdown
- [x] Include archived clients in search

## Acceptance criteria

- [x] Search by Instagram username returns matching client
- [x] Search by display name returns matching client
- [x] Clicking result opens client chat/card
"""

COMMENT = """## Completed

Client search and filtering is implemented on `main`.

### Backend
- `GET /api/clients/search/?q=` — search by Instagram username or display name
- Returns `chat_id`, `is_archived`, and assignee for each match
- Includes archived clients (no archive filter on search)
- Support managers only see clients from their assigned chats
- `apps/clients/search.py` — search service

### Frontend
- `ClientSearchBar` in dashboard header (`AppShell`)
- Debounced dropdown results with archived badge
- Clicking a result opens `/chats/<id>` (client card visible in chat sidebar)

### Verified
- 5 client search tests pass
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
            "User-Agent": "replyo-update-issue-17",
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
