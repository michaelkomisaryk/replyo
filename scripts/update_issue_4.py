#!/usr/bin/env python3
"""Update GitHub issue #4: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 4

UPDATED_BODY = """## Summary

Implement signup, login, and email verification per `docs/user-flows.md`.

## Tasks

- [x] Registration API (shop name, email, password)
- [x] Email verification flow
- [x] Login/logout and session or JWT auth
- [x] NextAuth.js integration against Django API
- [x] Signup and login UI pages
- [x] Protected routes on frontend

## Acceptance criteria

- [x] New shop owner can register and verify email
- [x] Authenticated user can access dashboard
- [x] Unauthenticated users are redirected to login
"""

COMMENT = """## Completed

User authentication and registration are implemented on `main`.

### Backend
- `POST /api/auth/register/` — creates shop + admin user, sends verification email
- `POST /api/auth/verify-email/` — verifies email via token
- `POST /api/auth/login/` — JWT login with email/password
- `POST /api/auth/logout/` — authenticated logout endpoint
- `GET /api/auth/me/` — current user profile
- `EmailVerificationToken` model and `is_email_verified` on `User`
- JWT auth via `djangorestframework-simplejwt`

### Frontend
- NextAuth.js credentials provider wired to Django login API
- `/signup`, `/login`, `/verify-email` pages
- Middleware protects dashboard routes and redirects unauthenticated users to `/login`
- Dashboard shows signed-in user and logout action

### Verified
- Register → verify email → login → `/api/auth/me/` flow works
- `npm run build` succeeds with auth routes and middleware
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
            "User-Agent": "replyo-update-issue-4",
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
