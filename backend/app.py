"""
Veris — Flask REST API
"""

import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from db import get_connection, init_db
from sources import ALLOWED_SOURCE_NAMES
from ranker import get_top_stories

load_dotenv()

app = Flask(__name__)

# Public read-only API — allow all origins unconditionally.
# No env var needed; CORS headers are always present regardless of deployment state.
CORS(app)

ALLOWED_SOURCES = ALLOWED_SOURCE_NAMES


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/articles")
def get_articles():
    """
    GET /api/articles
      ?source=AP|AFP|...  (optional)
      ?page=1             (1-based, default 1)
      ?per_page=20        (max 100)
    Returns articles from last 24 hours sorted by published_at DESC.
    """
    source_param = request.args.get("source", "").strip()
    try:
        page     = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers"}), 400

    if source_param and source_param not in ALLOWED_SOURCES:
        return jsonify({"error": f"source must be one of {sorted(ALLOWED_SOURCES)}"}), 400

    offset     = (page - 1) * per_page
    base_where = "published_at >= NOW() - INTERVAL '24 hours'"
    params: list = []

    if source_param:
        base_where += " AND source = %s"
        params.append(source_param)

    count_sql = f"SELECT COUNT(*) AS total FROM articles WHERE {base_where}"
    data_sql  = f"""
        SELECT id, title, source, published_at, url,
               craap_score, importance_score, importance_level, summary
        FROM   articles
        WHERE  {base_where}
        ORDER  BY published_at DESC
        LIMIT  %s OFFSET %s
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()["total"]
            cur.execute(data_sql, params + [per_page, offset])
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify({
        "articles": [_serialize(row) for row in rows],
        "meta": {
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "pages":    max(1, -(-total // per_page)),
        },
    })


@app.get("/api/top")
def get_top():
    """
    GET /api/top
      ?n=10   number of top stories to return (default 10, max 20)
    Returns top-n articles ranked by importance_score, source-diverse.
    """
    try:
        n = min(20, max(1, int(request.args.get("n", 10))))
    except ValueError:
        return jsonify({"error": "n must be an integer"}), 400

    stories = get_top_stories(n)
    return jsonify({
        "articles": [_serialize(row) for row in stories],
        "meta": {"total": len(stories)},
    })


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(row: dict) -> dict:
    pub = row["published_at"]
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return {
        "id":               row["id"],
        "title":            row["title"],
        "source":           row["source"],
        "published_at":     pub.isoformat(),
        "time_ago":         _time_ago(int((now - pub).total_seconds())),
        "url":              row["url"],
        "craap_score":      row.get("craap_score"),
        "importance_score": row.get("importance_score"),
        "importance_level": row.get("importance_level"),
        "summary":          row.get("summary"),
    }


def _time_ago(seconds: int) -> str:
    if seconds < 60:   return "just now"
    m = seconds // 60
    if m < 60:         return f"{m}m ago"
    h = m // 60
    if h < 24:         return f"{h}h ago"
    return             f"{h // 24}d ago"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=port)
