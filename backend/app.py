"""
Veris — Flask REST API
"""

import os
import re
from datetime import datetime, timezone
from collections import defaultdict

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

# Run DB migrations on startup so new columns are always present
# before the first request hits. All migrations use IF NOT EXISTS — safe
# to run on every Gunicorn worker start.
try:
    init_db()
except Exception as _e:
    import logging
    logging.getLogger(__name__).warning("init_db() failed at startup: %s", _e)


# ---------------------------------------------------------------------------
# Multi-source clustering — Truth Breakdown
# Groups articles covering the same event across different sources.
# Adds covered_by: ["BBC", "RFI"] to each article so the frontend can
# show which outlets independently reported the same story.
# ---------------------------------------------------------------------------

_STOP = {
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "was", "were", "be", "been", "has", "have", "had",
    "will", "would", "could", "should", "may", "might", "must", "can",
    "that", "this", "these", "those", "with", "from", "by", "as", "its",
    "it", "he", "she", "they", "we", "his", "her", "their", "our",
    "not", "no", "but", "if", "than", "then", "so", "up", "out",
    "after", "before", "over", "under", "into", "about", "says", "say",
    "said", "new", "two", "one", "first", "last", "more", "also",
}

_CLUSTER_THRESHOLD = 0.35   # Jaccard similarity — same story, different wording


def _title_tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z]+", title.lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cluster_articles(articles: list[dict]) -> list[dict]:
    """
    Attach covered_by list to each article — other sources that independently
    reported the same event within the same batch.
    O(n²) on titles — fine for our volumes (max ~200 articles per query).
    """
    if not articles:
        return articles

    tokens = [_title_tokens(a["title"]) for a in articles]

    # Union-find: each article starts in its own cluster
    parent = list(range(len(articles)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if _jaccard(tokens[i], tokens[j]) >= _CLUSTER_THRESHOLD:
                union(i, j)

    # Build cluster → [indices] map
    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(len(articles)):
        clusters[find(i)].append(i)

    # Attach covered_by to each article (sorted, excludes own source)
    result = []
    for i, article in enumerate(articles):
        cluster_indices = clusters[find(i)]
        covered_by = sorted({
            articles[j]["source"]
            for j in cluster_indices
            if articles[j]["source"] != article["source"]
        })
        result.append({**article, "covered_by": covered_by})

    return result


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

    serialized = _cluster_articles([_serialize(row) for row in rows])
    return jsonify({
        "articles": serialized,
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
    serialized = _cluster_articles([_serialize(row) for row in stories])
    return jsonify({
        "articles": serialized,
        "meta": {"total": len(serialized)},
    })


@app.get("/api/sources")
def get_sources():
    """
    GET /api/sources
    Returns the list of source names that have at least one article
    published in the last 24 hours. Used by the frontend to hide
    empty source tabs.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT source
                FROM   articles
                WHERE  published_at >= NOW() - INTERVAL '24 hours'
                ORDER  BY source
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify({"sources": [row["source"] for row in rows]})


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
        "covered_by":       row.get("covered_by", []),
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
