#!/usr/bin/env python3
"""Update GitHub issue #7: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 7

UPDATED_BODY = """## Summary

Allow shop admins to connect their Instagram business account via Meta OAuth.

## Tasks

- [x] Meta app configuration and OAuth flow
- [x] Store Instagram account tokens securely per shop
- [x] Connection status API and UI in settings
- [x] Admin-only permission to manage integration
- [x] Handle token refresh and disconnect

## Acceptance criteria

- [x] Admin can connect Instagram account from settings
- [x] Connection status visible in dashboard/settings
- [x] Only Admin role can manage integration

## References

- `docs/technical-requirements.md` — Meta Graph API
- `docs/user-roles.md`
"""

COMMENT = """## Completed

Instagram OAuth connection is implemented on `main`.

### Backend
- New `apps.integrations` app with `InstagramConnection` model
- Encrypted token storage via Django signing (tokens never exposed in API responses)
- `GET /api/integrations/instagram/status/` — safe connection status for shop members
- `GET /api/integrations/instagram/connect/` — Meta OAuth authorization URL (admin only)
- `GET /api/integrations/instagram/callback/` — OAuth callback, redirects to settings
- `POST /api/integrations/instagram/mock-connect/` — dev mock connect when Meta env is unset
- `POST /api/integrations/instagram/disconnect/` — admin disconnect
- `POST /api/integrations/instagram/refresh/` — admin token refresh (incl. mock tokens)
- Meta env vars: `META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI`

### Frontend
- `/settings` page with Instagram connect/disconnect/refresh UI
- Dashboard header badge shows Instagram connection status
- Onboarding checklist links to settings for Instagram step
- Settings nav item added to app shell

### Verified
- 11 Instagram integration API tests pass (16 total with onboarding updates)
- `npm run build` succeeds with `/settings` route
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
            "User-Agent": "replyo-update-issue-7",
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
