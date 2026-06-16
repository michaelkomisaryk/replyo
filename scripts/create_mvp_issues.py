#!/usr/bin/env python3
"""Create MVP GitHub issues for the Replyo repository."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "michaelkomisaryk/replyo"
API_BASE = f"https://api.github.com/repos/{REPO}"
API_URL = f"{API_BASE}/issues"

LABELS = {
    "setup": "Project scaffolding and tooling",
    "backend": "Django API and business logic",
    "frontend": "Next.js UI",
    "database": "Models and migrations",
    "auth": "Authentication and authorization",
    "integration": "Instagram / Meta API",
    "infrastructure": "Deployment and DevOps",
}

ISSUES = [
    {
        "title": "Bootstrap Django backend project",
        "labels": ["setup", "backend"],
        "body": """## Summary

Set up the initial Django backend according to `docs/technical-requirements.md`.

## Tasks

- [ ] Create Python project with Django 5.x and Django REST Framework
- [ ] Configure PostgreSQL and Django migrations
- [ ] Add environment-based settings (`.env` for dev/prod)
- [ ] Organize feature-based Django apps (`accounts`, `clients`, `messages`, `orders`)
- [ ] Add health-check endpoint (`GET /api/health/`)
- [ ] Document local setup in README

## Acceptance criteria

- `python manage.py runserver` starts without errors
- Migrations apply cleanly against local PostgreSQL
- Health endpoint returns 200 JSON response
""",
    },
    {
        "title": "Bootstrap Next.js frontend project",
        "labels": ["setup", "frontend"],
        "body": """## Summary

Set up the Next.js frontend according to `docs/technical-requirements.md`.

## Tasks

- [ ] Initialize Next.js (App Router) with TypeScript
- [ ] Configure Tailwind CSS
- [ ] Set up Zustand or React Query for server state
- [ ] Add base layout, routing, and API client for Django backend
- [ ] Configure environment variables for dev/prod
- [ ] Document local setup in README

## Acceptance criteria

- `npm run dev` starts without errors
- App connects to backend health endpoint
- Shared UI shell renders (header/sidebar placeholder)
""",
    },
    {
        "title": "Define core database models",
        "labels": ["backend", "database"],
        "body": """## Summary

Design and implement core Django models for the MVP domain.

## Models

- **Shop** — business account (name, settings)
- **User** — team member linked to shop with role
- **Client** — Instagram customer (username, display name, notes)
- **Chat** — conversation thread linked to client
- **Message** — individual message (inbound/outbound, timestamps)
- **Order** — order linked to client/chat with status

## Order statuses

`New Client`, `Waiting Payment`, `Paid`, `Sent`, `Completed`, `Rejected`

## Acceptance criteria

- Models and migrations created for all entities
- Foreign keys and indexes defined for common queries
- Django admin registered for debugging
- Basic serializers expose read endpoints
""",
    },
    {
        "title": "User authentication and registration",
        "labels": ["backend", "frontend", "auth"],
        "body": """## Summary

Implement signup, login, and email verification per `docs/user-flows.md`.

## Tasks

- [ ] Registration API (shop name, email, password)
- [ ] Email verification flow
- [ ] Login/logout and session or JWT auth
- [ ] NextAuth.js integration against Django API
- [ ] Signup and login UI pages
- [ ] Protected routes on frontend

## Acceptance criteria

- New shop owner can register and verify email
- Authenticated user can access dashboard
- Unauthenticated users are redirected to login
""",
    },
    {
        "title": "User roles and permissions system",
        "labels": ["backend", "auth"],
        "body": """## Summary

Implement role-based access per `docs/user-roles.md`.

## Roles

- **Admin** — full access
- **Manager** — chats, orders, client cards
- **Support Manager** — assigned chats only, read-only client cards

## Tasks

- [ ] Role field on User model
- [ ] DRF permission classes per role
- [ ] Enforce permissions on chat, order, and client endpoints
- [ ] Permission summary covered by API tests

## Acceptance criteria

- Admin can access all resources
- Support Manager cannot update orders or edit client cards
- Support Manager only sees assigned chats
""",
    },
    {
        "title": "Shop onboarding and team invitation",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Build post-registration onboarding per `docs/user-flows.md`.

## Tasks

- [ ] Onboarding checklist on first dashboard visit
- [ ] Invite team members (Manager, Support Manager) by email
- [ ] Accept invitation and set password flow
- [ ] Connect Instagram step placeholder in checklist

## Acceptance criteria

- New admin sees onboarding checklist after signup
- Admin can invite a team member who can then log in
- Checklist tracks completed steps
""",
    },
    {
        "title": "Instagram OAuth connection",
        "labels": ["integration", "backend"],
        "body": """## Summary

Allow shop admins to connect their Instagram business account via Meta OAuth.

## Tasks

- [ ] Meta app configuration and OAuth flow
- [ ] Store Instagram account tokens securely per shop
- [ ] Connection status API and UI in settings
- [ ] Admin-only permission to manage integration
- [ ] Handle token refresh and disconnect

## Acceptance criteria

- Admin can connect Instagram account from settings
- Connection status visible in dashboard/settings
- Only Admin role can manage integration

## References

- `docs/technical-requirements.md` — Meta Graph API
- `docs/user-roles.md`
""",
    },
    {
        "title": "Instagram webhooks and inbound message sync",
        "labels": ["integration", "backend"],
        "body": """## Summary

Receive Instagram DMs in real time and sync them into the CRM.

## Tasks

- [ ] Register Meta webhook endpoint
- [ ] Verify webhook signatures
- [ ] Parse inbound DM events and create/update Chat and Message records
- [ ] Link messages to existing Client by Instagram username
- [ ] Background job for periodic sync fallback

## Acceptance criteria

- Incoming Instagram DM creates or updates a chat in the database
- Messages appear in API within seconds of webhook delivery
- Duplicate events are handled idempotently

## References

- `docs/user-flows.md` — Chat Flow
- `docs/project-overview.md` — Instagram Integration
""",
    },
    {
        "title": "Send Instagram DM replies from CRM",
        "labels": ["integration", "backend", "frontend"],
        "body": """## Summary

Allow team members to reply to clients directly from MicroCRM.

## Tasks

- [ ] Send message API via Meta Graph API
- [ ] Store outbound messages in Message model
- [ ] Reply composer UI in chat detail view
- [ ] Handle API errors and rate limits gracefully
- [ ] Show send status (sending, sent, failed)

## Acceptance criteria

- Team member can send a reply from chat UI
- Reply is delivered to Instagram and stored in CRM
- Failed sends show actionable error to user

## References

- `docs/user-flows.md` — Seller Flow
""",
    },
    {
        "title": "Client cards with notes and order history",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Implement client management per MVP scope in `docs/project-overview.md`.

## Tasks

- [ ] Client card API (profile, Instagram username, notes)
- [ ] Add/edit notes on client card
- [ ] Display order history on client card
- [ ] Client card panel in chat detail view
- [ ] Admin/Manager can edit; Support Manager read-only

## Acceptance criteria

- Client card shows Instagram username and notes
- Order history listed on client card
- Permissions enforced per role
""",
    },
    {
        "title": "Order tracking with status workflow",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Implement order lifecycle per `docs/project-overview.md` and `docs/user-flows.md`.

## Statuses

`New Client`, `Waiting Payment`, `Paid`, `Sent`, `Completed`, `Rejected`

## Tasks

- [ ] Create order linked to client/chat
- [ ] Update order status API
- [ ] Order status UI in chat detail view
- [ ] Order creation from chat (Manager/Admin)
- [ ] Status change history (optional audit log)

## Acceptance criteria

- Manager can create order from a chat
- Status updates persist and reflect in UI
- Completed orders trigger chat priority change
""",
    },
    {
        "title": "Chat priority system (backend)",
        "labels": ["backend"],
        "body": """## Summary

Automatically categorize chats into priority buckets per `docs/chat-priority-system.md`.

## Priority buckets

1. **New Clients** — first message, no reply yet
2. **Waiting for Reply** — no response within time window (e.g. 1 hour)
3. **Active Orders** — confirmed order in progress
4. **Completed Orders** — delivered/closed
5. **Rejected Clients** — flagged or blocked

## Tasks

- [ ] Priority calculation service
- [ ] Scheduled job to recalculate wait times
- [ ] API returns chats grouped or tagged by priority
- [ ] Color-coded wait time metadata for Waiting for Reply

## Acceptance criteria

- New unreplied chat appears in New Clients bucket
- Chat moves to Waiting for Reply after threshold
- Active order chat appears in Active Orders bucket
""",
    },
    {
        "title": "Smart chat visibility and auto-archiving",
        "labels": ["backend"],
        "body": """## Summary

Control which chats appear on the dashboard per `docs/smart-chat-visibility.md`.

## Tasks

- [ ] Active/inactive chat logic (7-day window, open orders, pinned)
- [ ] Auto-archive completed orders after 24 hours
- [ ] Hide rejected clients from main view by default
- [ ] Auto-reactivate archived chat on new inbound message
- [ ] Archive search API

## Acceptance criteria

- Inactive chats hidden from main dashboard
- Completed order chats archive after 24 hours
- New message from archived client reactivates chat and triggers notification
""",
    },
    {
        "title": "Chat assignment and status updates",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Support team workflows from `docs/user-flows.md`.

## Tasks

- [ ] Assign chat to team member (Admin/Manager)
- [ ] Filter chats by assignee
- [ ] Manual chat status updates (e.g. Active Order, Completed)
- [ ] Pin chat to keep visible
- [ ] Escalate chat (Support Manager → Manager/Admin)

## Acceptance criteria

- Admin can assign chat to any team member
- Assigned chats visible to assignee
- Support Manager can escalate chat
""",
    },
    {
        "title": "Dashboard UI — prioritized chat list",
        "labels": ["frontend"],
        "body": """## Summary

Build the main dashboard view per MVP scope.

## Tasks

- [ ] Chat list grouped by priority buckets
- [ ] Show wait time and urgency indicators
- [ ] New clients and waiting-for-reply sections at top
- [ ] Filter tabs (all, active orders, archived, rejected)
- [ ] Empty states and loading skeletons
- [ ] Responsive layout for desktop

## Acceptance criteria

- Dashboard shows chats in priority order
- Wait time visible for Waiting for Reply chats
- User can switch between main filters
""",
    },
    {
        "title": "Chat detail view with reply composer",
        "labels": ["frontend"],
        "body": """## Summary

Build the conversation view for reading and replying to messages.

## Tasks

- [ ] Message thread UI (inbound/outbound styling)
- [ ] Reply composer with send button
- [ ] Client card sidebar/panel
- [ ] Order status widget
- [ ] Assignment and status controls
- [ ] Real-time or polling refresh for new messages

## Acceptance criteria

- Full message history visible in chat view
- User can compose and send reply
- Client card and order status visible alongside chat
""",
    },
    {
        "title": "Client search and filtering",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Search clients by name or Instagram username per MVP scope.

## Tasks

- [ ] Search API with name and Instagram username
- [ ] Search bar in dashboard header
- [ ] Search results page or dropdown
- [ ] Include archived clients in search

## Acceptance criteria

- Search by Instagram username returns matching client
- Search by display name returns matching client
- Clicking result opens client chat/card
""",
    },
    {
        "title": "Notifications — new messages and waiting reply reminders",
        "labels": ["backend", "frontend"],
        "body": """## Summary

Alert team members about messages needing attention per `docs/project-overview.md`.

## Tasks

- [ ] In-app notification model and API
- [ ] Trigger on new inbound message
- [ ] Trigger on waiting-for-reply threshold
- [ ] Notification bell/dropdown in UI
- [ ] Mark as read / dismiss
- [ ] Notify assigned manager or admin on reactivation

## Acceptance criteria

- New message creates in-app notification
- Chat waiting >1 hour triggers reminder notification
- User can view and dismiss notifications
""",
    },
    {
        "title": "Deploy MVP to production",
        "labels": ["infrastructure"],
        "body": """## Summary

Deploy frontend and backend per `docs/technical-requirements.md`.

## Tasks

- [ ] Deploy Django API to Railway or Render
- [ ] Deploy Next.js app to Vercel
- [ ] Configure production PostgreSQL
- [ ] Set environment variables for dev/staging/prod
- [ ] Configure Instagram webhook URL for production
- [ ] Smoke test end-to-end in production

## Acceptance criteria

- Production URLs accessible and serving the app
- Instagram webhooks reach production backend
- Database migrations run successfully in prod
""",
    },
]


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
        token = result.stdout.strip()
        return token or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def api_request(token: str, method: str, url: str, payload: dict | None = None) -> dict | list:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "replyo-create-issues",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 422 and payload and "labels" in url:
            raise
        if exc.code == 422 and payload and "issues" in url:
            raise
        raise


def ensure_labels(token: str) -> None:
    existing = {
        label["name"]
        for label in api_request(token, "GET", f"{API_BASE}/labels?per_page=100")
    }
    for name, description in LABELS.items():
        if name in existing:
            continue
        api_request(
            token,
            "POST",
            f"{API_BASE}/labels",
            {"name": name, "color": "1d76db", "description": description},
        )
        print(f"Created label: {name}")


def create_issue(token: str, issue: dict) -> dict:
    payload = json.dumps(
        {
            "title": issue["title"],
            "body": issue["body"],
            "labels": issue["labels"],
        }
    ).encode()
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "replyo-create-issues",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main() -> int:
    token = get_token()
    if not token:
        print("ERROR: Not authenticated. Run: gh auth login", file=sys.stderr)
        return 1

    ensure_labels(token)

    existing_titles = {
        issue["title"]
        for issue in api_request(token, "GET", f"{API_URL}?state=all&per_page=100")
    }

    created = []
    for issue in ISSUES:
        if issue["title"] in existing_titles:
            print(f"Skipped (exists): {issue['title']}")
            continue
        try:
            result = create_issue(token, issue)
            created.append((result["number"], result["html_url"], issue["title"]))
            print(f"Created #{result['number']}: {issue['title']}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            print(f"FAILED: {issue['title']} — {exc.code} {body[:300]}", file=sys.stderr)
            return 1

    print(f"\nCreated {len(created)} issues.")
    for number, url, title in created:
        print(f"  #{number} {title}\n    {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
