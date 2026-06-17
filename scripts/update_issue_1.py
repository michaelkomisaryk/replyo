#!/usr/bin/env python3
"""Update GitHub issue #1: check off tasks, comment, and close."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 1

UPDATED_BODY = """## Summary

Set up the initial Django backend according to `docs/technical-requirements.md`.

## Tasks

- [x] Create Python project with Django 5.x and Django REST Framework
- [x] Configure PostgreSQL and Django migrations
- [x] Add environment-based settings (`.env` for dev/prod)
- [x] Organize feature-based Django apps (`accounts`, `clients`, `messages`, `orders`)
- [x] Add health-check endpoint (`GET /api/health/`)
- [x] Document local setup in README

## Acceptance criteria

- [x] `python manage.py runserver` starts without errors
- [x] Database migrations apply cleanly against local PostgreSQL
- [x] Health endpoint returns 200 JSON response
"""

COMMENT = """## Completed

Bootstrap Django backend is implemented on `main`.

### Delivered
- Django 5.x + DRF project under `backend/`
- Feature apps: `accounts`, `clients`, `messages`, `orders`, plus `common` for shared views
- Environment-based settings via `.env` / `.env.example` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DATABASE_URL`)
- PostgreSQL support via `dj-database-url` + `psycopg`; `docker-compose.yml` for local Postgres
- SQLite fallback when `DATABASE_URL` is unset (quick local dev)
- Health endpoint: `GET /api/health/` → `{"status": "ok"}`
- README with setup, migrate, and runserver instructions

### Verified
- `python backend/manage.py check` — no issues
- `python backend/manage.py migrate` — applied successfully
- `python backend/manage.py runserver` — starts without errors
- `curl http://127.0.0.1:8000/api/health/` — HTTP 200

### Notes
- `apps.messages` uses label `crm_messages` to avoid conflict with Django's built-in `messages` app.
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
            "User-Agent": "replyo-update-issue-1",
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

    api_request(
        token,
        "POST",
        f"{base}/comments",
        {"body": COMMENT},
    )
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
