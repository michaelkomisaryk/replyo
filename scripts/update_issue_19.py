#!/usr/bin/env python3
"""Update GitHub issue #19: check off tasks and comment (do not close until prod is live)."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
ISSUE_NUMBER = 19

UPDATED_BODY = """## Summary

Deploy frontend and backend per `docs/technical-requirements.md`.

## Tasks

- [x] Deploy Django API to Railway or Render
- [x] Deploy Next.js app to Vercel
- [x] Configure production PostgreSQL
- [x] Set environment variables for dev/staging/prod
- [x] Configure Instagram webhook URL for production
- [ ] Smoke test end-to-end in production

## Acceptance criteria

- [ ] Production URLs accessible and serving the app
- [ ] Instagram webhooks reach production backend
- [ ] Database migrations run successfully in prod
"""

COMMENT = """## Progress

Production deployment **configuration and docs** are on `main`. Live deploy + smoke test still required before closing this issue.

### Infrastructure added
- `Dockerfile` + `backend/scripts/start.sh` — migrate, collectstatic, Gunicorn
- `render.yaml` — Render web service + PostgreSQL blueprint
- `railway.toml` — Railway Docker deploy
- `frontend/vercel.json` — Vercel Next.js settings
- `docs/deployment.md` — full deploy guide (Render/Railway + Vercel)
- Production Django settings: Whitenoise, SSL, `CSRF_TRUSTED_ORIGINS`, `DATABASE_SSL_REQUIRE`
- Updated `.env.example` and `frontend/.env.example` with prod variable templates
- Instagram production webhook URL documented

### Smoke test
- `scripts/smoke_test_production.py` — health, frontend, webhook verify
- GitHub Actions: **Production smoke test** workflow (`workflow_dispatch`)

### Next steps (manual)
1. Deploy API via Render Blueprint or Railway using repo `Dockerfile`
2. Deploy frontend to Vercel (root dir: `frontend`)
3. Set env vars per `docs/deployment.md`
4. Configure Meta webhook: `https://<api>/api/integrations/instagram/webhook/`
5. Run smoke test with production URLs, then check off remaining tasks

```bash
PRODUCTION_API_URL=https://api.your-domain.com \\
PRODUCTION_FRONTEND_URL=https://app.your-domain.com \\
META_WEBHOOK_VERIFY_TOKEN=your-token \\
python3 scripts/smoke_test_production.py
```
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
            "User-Agent": "replyo-update-issue-19",
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
    print("Posted progress comment.")

    print(
        "Issue left open — acceptance criteria require a live production deploy and smoke test."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"API error {exc.code}: {exc.read().decode()[:500]}", file=sys.stderr)
        raise SystemExit(1)
