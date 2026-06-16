# Technical Requirements

## Frontend

- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand or React Query
- **Auth:** NextAuth.js (against Django API)

## Backend

- **Runtime:** Python 3.12+
- **Framework:** Django
- **API:** Django REST Framework
- **Language:** Python
- **Architecture:** Feature-based Django apps
- **ORM:** Django ORM

## Database

- **Primary DB:** PostgreSQL
- **Migrations:** Django migrations

## Infrastructure

- **Hosting:** Vercel (frontend), Railway or Render (backend)
- **Environment:** `.env` files with separate configs for dev/prod

## Integrations

- **Instagram API:** Meta Graph API for reading and sending DMs
- **Webhooks:** For real-time message sync from Instagram

## Code Standards

- TypeScript on the frontend, Python on the backend
- Feature-based folder structure (Django apps)
- Reusable frontend components
- Server Actions where possible on the frontend
- Django conventions for models, views, and serializers
