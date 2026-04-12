"""
Veris — AI Importance Ranker

Uses Ollama (local, open-source, free) to classify article importance.
No article content is rewritten or summarised — CLASSIFICATION ONLY.

Importance levels:
  5 — Breaking  : Major world event, immediate global/national impact
  4 — Critical  : Significant development, wide-ranging consequences
  3 — Important : Notable news, meaningful regional/national impact
  2 — Standard  : Routine coverage, limited immediate impact
  1 — Low       : Minor development, niche or soft news

Model: llama3.2:1b (default — fast, 1.3 GB)
       Swap OLLAMA_MODEL to phi3:mini for higher accuracy (~4 GB)

Fallback: deterministic keyword heuristic — used automatically when
          Ollama is not running (e.g. GitHub Actions).
"""

import json
import logging
import time

import requests
from db import get_connection

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"   # change to phi3:mini for better accuracy

LEVELS = {
    5: "Breaking",
    4: "Critical",
    3: "Important",
    2: "Standard",
    1: "Low",
}

# Tight prompt — asks for JSON only, no prose, low temperature
_PROMPT = """\
You are a senior news editor. Rate the newsworthiness of the headline below.

Scale:
5 = Breaking  — war, mass-casualty disaster, assassination, major election result, pandemic declaration
4 = Critical  — major policy change, large-scale unrest, significant court ruling, major economic shift
3 = Important — notable political development, significant regional event, meaningful social issue
2 = Standard  — routine announcement, minor development, follow-up story
1 = Low       — soft news, niche interest, minor local event

Headline: "{title}"
Source: {source}

Reply with ONLY valid JSON, no explanation:
{{"score": <integer 1-5>, "level": "<Breaking|Critical|Important|Standard|Low>"}}\
"""


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

def _ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_rank(title: str, source: str) -> dict | None:
    prompt = _PROMPT.format(title=title, source=source)
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model":   OLLAMA_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "format":  "json",
                "options": {"temperature": 0.05, "seed": 42},
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "{}")
        data = json.loads(raw)
        score = int(data.get("score", 0))
        if 1 <= score <= 5:
            return {"score": score, "level": LEVELS[score], "ai": True, "method": "ai"}
    except Exception as e:
        log.debug("Ollama error: %s", e)
    return None


# ---------------------------------------------------------------------------
# Heuristic fallback (deterministic, no AI needed)
# ---------------------------------------------------------------------------

_BREAKING = {
    "killed", "dead", "deaths", "war", "attack", "explosion", "blast",
    "earthquake", "hurricane", "tsunami", "flood", "wildfire", "coup",
    "assassination", "assassinated", "pandemic", "outbreak", "invasion",
    "nuclear", "ceasefire", "ceasefire", "hostage",
}
_CRITICAL = {
    "election", "elected", "sanctions", "recession", "arrested", "protest",
    "treaty", "crisis", "emergency", "ban", "indicted", "impeach",
    "collapse", "summit", "missile", "troops", "military",
}
_IMPORTANT = {
    "government", "parliament", "minister", "president", "report",
    "investigation", "trial", "verdict", "ruling", "policy", "reform",
    "climate", "inflation", "budget", "agreement", "deal",
}


def _heuristic_rank(title: str) -> dict:
    words = set(title.lower().replace("-", " ").split())
    if words & _BREAKING:
        return {"score": 5, "level": "Breaking", "ai": False, "method": "heuristic"}
    if words & _CRITICAL:
        return {"score": 4, "level": "Critical",  "ai": False, "method": "heuristic"}
    if words & _IMPORTANT:
        return {"score": 3, "level": "Important", "ai": False, "method": "heuristic"}
    return {"score": 2, "level": "Standard", "ai": False, "method": "heuristic"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rank_article(title: str, source: str) -> dict:
    """Score a single article. Uses Ollama if available, heuristic otherwise."""
    result = _ollama_rank(title, source)
    if result:
        return result
    return _heuristic_rank(title)


def rank_unranked_articles(limit: int = 100) -> int:
    """
    Score articles from the DB in two passes:

    Pass 1 — Never ranked (importance_score IS NULL):
              Includes BOTH newly scraped articles AND any older stored
              articles that were never processed. No time-window limit.

    Pass 2 — Heuristic-ranked articles (ranked_by = 'heuristic'):
              If Ollama is now available, upgrade these to AI scores.
              Only re-ranks articles from the last 7 days so the job
              stays bounded.

    Returns total number of articles scored/upgraded.
    """
    use_ai = _ollama_available()
    log.info(
        "Ollama %s — %s",
        "available" if use_ai else "offline",
        f"AI ranking with {OLLAMA_MODEL}" if use_ai else "keyword heuristic fallback",
    )

    conn = get_connection()
    try:
        with conn.cursor() as cur:

            # --- Pass 1: never ranked (all stored articles, no time cap) ---
            cur.execute("""
                SELECT id, title, source
                FROM   articles
                WHERE  importance_score IS NULL
                ORDER  BY published_at DESC
                LIMIT  %s
            """, (limit,))
            unranked = cur.fetchall()

            # --- Pass 2: upgrade heuristic → AI (last 7 days, AI only) ---
            heuristic_rows = []
            if use_ai:
                cur.execute("""
                    SELECT id, title, source
                    FROM   articles
                    WHERE  ranked_by = 'heuristic'
                      AND  published_at > NOW() - INTERVAL '7 days'
                    ORDER  BY published_at DESC
                    LIMIT  %s
                """, (limit,))
                heuristic_rows = cur.fetchall()

        rows = list(unranked) + list(heuristic_rows)

        if not rows:
            log.info("Nothing to rank.")
            return 0

        log.info(
            "Ranking %d articles (%d new, %d heuristic upgrades)...",
            len(rows), len(unranked), len(heuristic_rows),
        )
        ranked = 0

        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    result = rank_article(row["title"], row["source"])
                    method = "ai" if result["ai"] else "heuristic"
                    cur.execute(
                        """
                        UPDATE articles
                           SET importance_score = %s,
                               importance_level = %s,
                               ranked_by        = %s
                         WHERE id = %s
                        """,
                        (result["score"], result["level"], method, row["id"]),
                    )
                    ranked += 1
                    log.debug(
                        "  [%s/%s] %-8s %s",
                        method.upper()[:2],
                        row["source"],
                        result["level"],
                        row["title"][:70],
                    )
                    if use_ai:
                        time.sleep(0.05)

        log.info("Ranking complete — %d articles scored.", ranked)
        return ranked
    finally:
        conn.close()


def get_top_stories(n: int = 10) -> list[dict]:
    """
    Return the top-n articles from the last 24 h by importance_score.
    Applies source diversity cap: max 3 articles per source.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, source, published_at, url,
                       craap_score, importance_score, importance_level
                FROM   articles
                WHERE  published_at > NOW() - INTERVAL '24 hours'
                  AND  importance_score IS NOT NULL
                ORDER  BY importance_score DESC, craap_score DESC, published_at DESC
                LIMIT  100
            """)
            rows = cur.fetchall()

        seen: dict[str, int] = {}
        top = []
        for row in rows:
            src = row["source"]
            if seen.get(src, 0) >= 3:
                continue
            seen[src] = seen.get(src, 0) + 1
            top.append(dict(row))
            if len(top) >= n:
                break
        return top
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rank_unranked_articles()
