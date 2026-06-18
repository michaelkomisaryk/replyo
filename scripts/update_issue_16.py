#!/usr/bin/env python3
"""Update GitHub issue #16: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 16

UPDATED_BODY = """## Summary

Support team workflows from `docs/user-flows.md`.

## Tasks

- [x] Assign chat to team member (Admin/Manager)
- [x] Filter chats by assignee
- [x] Manual chat status updates (e.g. Active Order, Completed)
- [x] Pin chat to keep visible
- [x] Escalate chat (Support Manager → Manager/Admin)

## Acceptance criteria

- [x] Admin can assign chat to any team member
- [x] Assigned chats visible to assignee
- [x] Support Manager can escalate chat
"""

COMMENT = """## Completed

Chat assignment and status updates are implemented on `main`.

### Backend
- `POST /api/chats/<id>/assign/` — admin/manager assign or unassign any team member
- `POST /api/chats/<id>/escalate/` — support manager escalates; notifies admins/managers
- `GET /api/chats/?assigned_to=<id|me|unassigned>` — filter chat list by assignee
- `GET /api/chats/priorities/?assigned_to=...` — same filter on prioritized dashboard
- `GET /api/users/?team=1` — team list for assignment UI
- `apps/messages/assignee.py` — assignee filtering and escalation notifications

### Frontend
- `ChatControls` — assign, pin, archive, escalate from chat detail
- `AssigneeFilter` on `/chats` dashboard — filter by team member, me, or unassigned
- `ChatRow` shows assignee email
- `OrderStatusPanel` — manual order/chat status updates (Active Order, Completed, etc.)

### Verified
- 8 chat assignment tests pass
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
            "User-Agent": "replyo-update-issue-16",
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
