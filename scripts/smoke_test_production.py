#!/usr/bin/env python3
"""Smoke test production deployment URLs."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _get(url: str) -> tuple[int, dict | str]:
    request = urllib.request.Request(url, headers={"User-Agent": "replyo-smoke-test"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode()
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body[:500]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:500]
        return exc.code, body


def main() -> int:
    api_url = os.environ.get("PRODUCTION_API_URL", "").rstrip("/")
    frontend_url = os.environ.get("PRODUCTION_FRONTEND_URL", "").rstrip("/")
    webhook_token = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "")

    if not api_url:
        print("ERROR: Set PRODUCTION_API_URL", file=sys.stderr)
        return 1

    failures = 0

    status, payload = _get(f"{api_url}/api/health/")
    if status == 200 and isinstance(payload, dict) and payload.get("status") == "ok":
        print(f"OK  API health ({api_url}/api/health/)")
    else:
        print(f"FAIL API health: status={status} body={payload}", file=sys.stderr)
        failures += 1

    if frontend_url:
        status, _body = _get(frontend_url)
        if status == 200:
            print(f"OK  Frontend ({frontend_url})")
        else:
            print(f"FAIL Frontend: status={status}", file=sys.stderr)
            failures += 1

    if webhook_token:
        challenge = "replyo-smoke-challenge"
        params = urllib.parse.urlencode(
            {
                "hub.mode": "subscribe",
                "hub.verify_token": webhook_token,
                "hub.challenge": challenge,
            }
        )
        status, body = _get(f"{api_url}/api/integrations/instagram/webhook/?{params}")
        if status == 200 and body == challenge:
            print("OK  Instagram webhook verification")
        else:
            print(
                f"FAIL Webhook verify: status={status} body={body!r}",
                file=sys.stderr,
            )
            failures += 1

    if failures:
        print(f"\n{failures} check(s) failed.", file=sys.stderr)
        return 1

    print("\nAll smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
