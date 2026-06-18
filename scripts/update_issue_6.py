#!/usr/bin/env python3
"""Update GitHub issue #6: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 6

UPDATED_BODY = """## Summary

Build post-registration onboarding per `docs/user-flows.md`.

## Tasks

- [x] Onboarding checklist on first dashboard visit
- [x] Invite team members (Manager, Support Manager) by email
- [x] Accept invitation and set password flow
- [x] Connect Instagram step placeholder in checklist

## Acceptance criteria

- [x] New admin sees onboarding checklist after signup
- [x] Admin can invite a team member who can then log in
- [x] Checklist tracks completed steps
"""

COMMENT = """## Completed

Shop onboarding and team invitation are implemented on `main`.

### Backend
- `GET /api/onboarding/` — checklist with email, Instagram placeholder, and team invite steps
- `POST /api/invitations/` — admin invites Manager or Support Manager by email
- `GET /api/invitations/` — list shop invitations
- `POST /api/invitations/accept/` — accept invite and set password
- `TeamInvitation` model with email token flow

### Frontend
- `OnboardingChecklist` on dashboard with progress counter
- Admin invite form embedded in checklist
- `/accept-invite` page for invited teammates
- Instagram step shown as placeholder for a future integration

### Verified
- 5 onboarding API tests pass (14 total accounts tests)
- `npm run build` succeeds with new routes
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
            "User-Agent": "replyo-update-issue-6",
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
