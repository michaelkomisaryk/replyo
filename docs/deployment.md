# Deployment

Deploy Replyo per `docs/technical-requirements.md`: **Vercel** (frontend) and **Render** or **Railway** (Django API + PostgreSQL).

## Architecture

| Component | Platform | Notes |
|-----------|----------|-------|
| Next.js frontend | Vercel | Root directory: `frontend` |
| Django API | Render or Railway | Docker image from repo root `Dockerfile` |
| PostgreSQL | Render Postgres or Railway plugin | Set `DATABASE_URL` |

## 1. Deploy backend (Render)

1. Create a Render account and connect this GitHub repo.
2. Use **New → Blueprint** and select `render.yaml`, or create a **Web Service** manually:
   - Runtime: Docker
   - Dockerfile path: `./Dockerfile`
   - Health check path: `/api/health/`
3. Add a **PostgreSQL** database and link `DATABASE_URL` to the web service.
4. Set environment variables (see [Environment variables](#environment-variables)).
5. Deploy. On each deploy, `backend/scripts/start.sh` runs migrations and starts Gunicorn.

### Railway (alternative)

1. Create a Railway project from this repo.
2. Add a **PostgreSQL** service and link `DATABASE_URL` to the web service.
3. Railway uses `railway.toml` + root `Dockerfile`.
4. Set the same environment variables as Render.

## 2. Deploy frontend (Vercel)

1. Import the repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Configure environment variables (see below).
4. Deploy. Vercel uses `frontend/vercel.json`.

## 3. Environment variables

### Backend (Render / Railway)

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql://...` | Yes (prod) |
| `DATABASE_SSL_REQUIRE` | `true` | Yes (managed Postgres) |
| `DJANGO_SECRET_KEY` | random 50+ chars | Yes |
| `DJANGO_DEBUG` | `false` | Yes |
| `DJANGO_ALLOWED_HOSTS` | `api.replyo.example.com` | Yes |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` | Yes |
| `CORS_ALLOWED_ORIGINS` | `https://app.replyo.example.com` | Yes |
| `CSRF_TRUSTED_ORIGINS` | `https://app.replyo.example.com` | Yes |
| `FRONTEND_URL` | `https://app.replyo.example.com` | Yes |
| `META_APP_ID` | Meta app ID | For Instagram |
| `META_APP_SECRET` | Meta app secret | For Instagram |
| `META_REDIRECT_URI` | `https://api.../api/integrations/instagram/callback/` | For Instagram |
| `META_WEBHOOK_VERIFY_TOKEN` | random string | For Instagram webhooks |

### Frontend (Vercel)

| Variable | Example | Required |
|----------|---------|----------|
| `NEXT_PUBLIC_API_URL` | `https://api.replyo.example.com` | Yes |
| `NEXTAUTH_URL` | `https://app.replyo.example.com` | Yes |
| `NEXTAUTH_SECRET` | random 32+ chars | Yes |

Copy from `.env.example` (backend) and `frontend/.env.example` for local dev values.

## 4. Instagram webhook (production)

In the [Meta Developer Console](https://developers.facebook.com/):

1. **Callback URL:** `https://<your-api-domain>/api/integrations/instagram/webhook/`
2. **Verify token:** same value as `META_WEBHOOK_VERIFY_TOKEN`
3. Subscribe to `messages` (and related) webhook fields for your Instagram app.

OAuth redirect URI for production:

`https://<your-api-domain>/api/integrations/instagram/callback/`

## 5. Smoke test

After both services are live, run:

```bash
export PRODUCTION_API_URL=https://api.replyo.example.com
export PRODUCTION_FRONTEND_URL=https://app.replyo.example.com
python3 scripts/smoke_test_production.py
```

Optional webhook check (requires `META_WEBHOOK_VERIFY_TOKEN`):

```bash
export META_WEBHOOK_VERIFY_TOKEN=your-token
python3 scripts/smoke_test_production.py
```

GitHub Actions: run the **Production smoke test** workflow manually with your URLs.

## 6. Scheduled jobs (production)

Run these on a cron schedule against the production database (Render cron, Railway cron, or external scheduler):

```bash
python backend/manage.py archive_inactive_chats
python backend/manage.py recalculate_chat_priorities
python backend/manage.py send_waiting_reply_reminders
python backend/manage.py sync_instagram_inbound
```

## Acceptance checklist

- [ ] `GET https://<api>/api/health/` returns `{"status":"ok","database":"ok"}`
- [ ] Frontend loads at `https://<app>/`
- [ ] Meta webhook verification succeeds (GET challenge)
- [ ] `migrate` completed on deploy (check Render/Railway logs)
