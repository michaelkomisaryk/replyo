## Replyo Backend Setup

This repository includes a Django backend scaffold in `backend/`.

### 1) Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
```

For PostgreSQL, start the database and set `DATABASE_URL` in `.env`:

```bash
docker compose up -d
```

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/replyo
```

If `DATABASE_URL` is not set, Django uses local SQLite for quick bootstrapping.

### 4) Run migrations

```bash
python backend/manage.py migrate
```

### 5) Start server

```bash
python backend/manage.py runserver
```

### Health check

`GET /api/health/` returns:

```json
{"status":"ok"}
```
