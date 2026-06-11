# Technical Requirements

## Application

- **Framework:** Django
- **Language:** Python 3.12+
- **UI:** Django templates + HTMX (progressive enhancement)
- **Styling:** Tailwind CSS (via django-tailwind or static build)
- **API (where needed):** Django REST Framework
- **Auth:** Django auth + django-allauth (email + Instagram OAuth)

## Backend

- **Architecture:** Django apps per feature (chats, clients, orders, notifications)
- **ORM:** Django ORM
- **Background jobs:** Celery + Redis (message sync, reminders)
- **Real-time updates:** Django Channels or HTMX polling (inbox refresh)

## Database

- **Primary DB:** PostgreSQL
- **Migrations:** Django migrations (`manage.py migrate`)

## Infrastructure

- **Hosting:** Railway, Render, or Fly.io
- **Static files:** WhiteNoise or object storage (S3-compatible)
- **Environment:** `.env` files with separate configs for dev/prod

## Integrations

- **Instagram API:** Meta Graph API for reading and sending DMs
- **Webhooks:** Django views for real-time message sync from Instagram

## Code Standards

- Python everywhere — follow PEP 8
- Feature-based Django app structure
- Reusable template components (partials)
- Type hints where practical
- Tests with pytest-django
