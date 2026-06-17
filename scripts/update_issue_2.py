#!/usr/bin/env python3
"""Update GitHub issue #2: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 2

UPDATED_BODY = """## Summary

Set up the Next.js frontend according to `docs/technical-requirements.md`.

## Tasks

- [x] Initialize Next.js (App Router) with TypeScript
- [x] Configure Tailwind CSS
- [x] Set up Zustand or React Query for server state
- [x] Add base layout, routing, and API client for Django backend
- [x] Configure environment variables for dev/prod
- [x] Document local setup in README

## Acceptance criteria

- [x] `npm run dev` starts without errors
- [x] App connects to backend health endpoint
- [x] Shared UI shell renders (header/sidebar placeholder)
"""

COMMENT = """## Completed

Next.js frontend bootstrap is implemented on `main`.

### Delivered
- Next.js App Router + TypeScript project under `frontend/`
- Tailwind CSS configured via the default Next.js template
- React Query provider and health-check query wired to Django API
- Shared UI shell with header and sidebar placeholders (`AppShell`)
- API client in `frontend/src/lib/api.ts` using `NEXT_PUBLIC_API_URL`
- `frontend/.env.example` for dev/prod configuration
- README frontend setup instructions
- Django CORS enabled for local frontend origins

### Verified
- `npm run dev` starts without errors
- `npm run build` completes successfully
- Dashboard shell renders at `http://127.0.0.1:3000`
- Frontend fetches `GET /api/health/` and displays backend status when Django is running
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
            "User-Agent": "replyo-update-issue-2",
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
