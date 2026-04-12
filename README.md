# Veris

A fast, minimal news aggregator pulling only from **Reuters**, **AP**, and **AFP** — no summaries, no opinions, no noise.

---

## Project Structure

```
NewsAPP/
├── backend/
│   ├── app.py          # Flask REST API
│   ├── scraper.py      # RSS ingestion pipeline
│   ├── db.py           # PostgreSQL connection + schema bootstrap
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── hooks/useArticles.js
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── FilterTabs.jsx
│   │       ├── ArticleCard.jsx
│   │       ├── SkeletonCard.jsx
│   │       ├── ErrorBanner.jsx
│   │       └── InfiniteScrollSentinel.jsx
│   ├── public/index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── .github/workflows/
│   └── pipeline.yml    # GitHub Actions cron (every 3 hours)
├── .env.example
└── README.md
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker | 20+ (for the database) |

---

## 1 — Database setup (Docker)

No local Postgres install needed. The `docker-compose.yml` spins up a single container with a named volume so data persists across restarts.

```bash
# Start the database container in the background
docker compose up -d db

# Verify it's healthy
docker compose ps
```

Default connection string (already set in `.env.example`):
```
postgresql://signalnews:signalnews@localhost:5432/signalnews
```

To stop the container without losing data:
```bash
docker compose stop db
```

To wipe the database and start fresh:
```bash
docker compose down -v
```

---

## 2 — Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — set DATABASE_URL to your PostgreSQL connection string

# Bootstrap the schema
python db.py

# Run a one-off scrape (populates the DB immediately)
python scraper.py

# Start the API server
python app.py
# → http://localhost:5000
```

---

## 3 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# (Optional) point at a remote API
# Create frontend/.env.local and add:
# REACT_APP_API_URL=http://localhost:5000/api

# Start the dev server
npm start
# → http://localhost:3000
```

The `"proxy": "http://localhost:5000"` in `package.json` forwards `/api/*` calls to the Flask backend during development, so no `.env.local` is needed locally.

---

## 4 — API reference

### `GET /api/articles`

Returns articles from the last 24 hours, sorted newest-first.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | string | — | Filter: `Reuters`, `AP`, or `AFP` |
| `page` | int | 1 | Page number (1-based) |
| `per_page` | int | 20 | Results per page (max 100) |

**Response**

```json
{
  "articles": [
    {
      "id": 1,
      "title": "…",
      "source": "Reuters",
      "published_at": "2025-04-11T09:00:00+00:00",
      "time_ago": "3h ago",
      "url": "https://…"
    }
  ],
  "meta": {
    "total": 142,
    "page": 1,
    "per_page": 20,
    "pages": 8
  }
}
```

### `GET /api/health`

```json
{ "status": "ok", "time": "2025-04-11T12:00:00+00:00" }
```

---

## 5 — GitHub Actions (automated ingestion)

The workflow at `.github/workflows/pipeline.yml` runs `scraper.py` every 3 hours.

**Setup:**

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions**.
3. Add a secret named `DATABASE_URL` with your production PostgreSQL URL.

The job can also be triggered manually from the **Actions** tab.

---

## 6 — Production deployment notes

- **Backend**: Deploy with `gunicorn app:app` behind nginx or on Railway/Render/Fly.io.
- **Frontend**: Run `npm run build` and serve the `build/` folder from a CDN (Vercel, Netlify, S3+CloudFront).
- **Database**: Use a managed PostgreSQL service (Supabase free tier, Railway, Neon).
- **CORS**: Set `CORS_ORIGIN` in your backend `.env` to the production frontend URL.
