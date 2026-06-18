#!/usr/bin/env python3
"""Update GitHub issue #10: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 10

UPDATED_BODY = """## Summary

Implement client management per MVP scope in `docs/project-overview.md`.

## Tasks

- [x] Client card API (profile, Instagram username, notes)
- [x] Add/edit notes on client card
- [x] Display order history on client card
- [x] Client card panel in chat detail view
- [x] Admin/Manager can edit; Support Manager read-only

## Acceptance criteria

- [x] Client card shows Instagram username and notes
- [x] Order history listed on client card
- [x] Permissions enforced per role
"""

COMMENT = """## Completed

Client cards with notes and order history are implemented on `main`.

### Backend
- `GET /api/clients/<id>/card/` — client profile with Instagram username, notes, and order history
- `PATCH /api/clients/<id>/card/` — update notes (admin/manager only)
- `can_edit` flag in response for frontend permission gating
- `GET /api/orders/?client=<id>` — filter orders by client

### Frontend
- `ClientCardPanel` sidebar in chat detail view (`/chats/[id]`)
- Editable notes for admin/manager; read-only for support manager
- Order history list with status labels

### Verified
- 4 client card API tests pass (plus existing role permission tests)
- `npm run build` succeeds
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
            "User-Agent": "replyo-update-issue-10",
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
