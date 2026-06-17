## Replyo Setup

This repository includes:
- Django backend in `backend/`
- Next.js frontend in `frontend/`

## Backend

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

### 5) Start backend server

```bash
python backend/manage.py runserver
```

### Health check

`GET /api/health/` returns:

```json
{"status":"ok"}
```

## Frontend

### 1) Install dependencies

```bash
cd frontend
npm install
```

### 2) Configure environment

```bash
cp .env.example .env.local
```

Default API URL:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3) Start frontend server

```bash
npm run dev
```

Open `http://127.0.0.1:3000`. The dashboard shell should render and show backend connection status from `/api/health/`.
