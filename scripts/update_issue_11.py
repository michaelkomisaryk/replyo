#!/usr/bin/env python3
"""Update GitHub issue #11: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 11

UPDATED_BODY = """## Summary

Implement order lifecycle per `docs/project-overview.md` and `docs/user-flows.md`.

## Statuses

`New Client`, `Waiting Payment`, `Paid`, `Sent`, `Completed`, `Rejected`

## Tasks

- [x] Create order linked to client/chat
- [x] Update order status API
- [x] Order status UI in chat detail view
- [x] Order creation from chat (Manager/Admin)
- [x] Status change history (optional audit log)

## Acceptance criteria

- [x] Manager can create order from a chat
- [x] Status updates persist and reflect in UI
- [x] Completed orders trigger chat priority change
"""

COMMENT = """## Completed

Order tracking with status workflow is implemented on `main`.

### Backend
- `POST /api/chats/<id>/orders/` — create order linked to chat/client (admin/manager)
- `PATCH /api/orders/<id>/` — update order status with audit log
- `GET /api/orders/<id>/history/` — status change history
- `GET /api/orders/?chat=<id>` — orders for a chat
- `OrderStatusChange` model records from/to status and user
- `Chat.priority` field synced when orders are created/completed (active vs completed buckets)

### Frontend
- `OrderStatusPanel` in chat detail — create order, status dropdown, priority label
- Status updates refresh client card order history

### Verified
- 6 order workflow tests pass
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
            "User-Agent": "replyo-update-issue-11",
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
