"""
Veris — Article Summariser

Generates a 3–4 sentence plain-English summary for each article so
users understand the story without leaving the app.

Primary:  Ollama (llama3.2:1b) — context-aware summary from title + RSS excerpt
Fallback: RSS excerpt stored at scrape time — used automatically in
          GitHub Actions where Ollama is unavailable.

Two passes per pipeline run:
  Pass 1 — articles with summary IS NULL (never summarised)
  Pass 2 — articles summarised_by = 'rss' in last 48 h
            upgraded to AI summary when Ollama becomes available
"""

import logging
import time

import requests
from db import get_connection

log = logging.getLogger(__name__)

OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"

_PROMPT = """\
You are a news summariser for Veris, a geopolitics-focused news aggregator.

Write a factual summary of this article in 3–4 sentences.

Rules:
- Cover the main event, who is involved, and why it matters geopolitically
- Include specific names, numbers, countries, and dates when available
- No opinion, no editorialising, no value judgements
- Do not start with "The article...", "According to...", or "This article..."
- Write in plain, direct English — as if briefing a busy analyst
- If the excerpt is too thin to summarise, write what you can from the headline

Headline: {title}
Source: {source}
Excerpt: {excerpt}

Write ONLY the summary, no preamble, no labels:"""


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

def _ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_summarise(title: str, source: str, excerpt: str) -> str | None:
    prompt = _PROMPT.format(
        title=title,
        source=source,
        excerpt=excerpt[:2000] if excerpt else "(no excerpt available)",
    )
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model":   OLLAMA_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": 0.2, "seed": 42},
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        # Sanity check — reject obviously bad outputs
        if len(text) > 40 and not text.lower().startswith("i "):
            return text
    except Exception as e:
        log.debug("Ollama summarise error: %s", e)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarise_articles(limit: int = 100) -> int:
    """
    Summarise articles that don't yet have a summary, or upgrade
    RSS-excerpt fallbacks to proper AI summaries.

    Pass 1 — summary IS NULL (never summarised):
              Use Ollama if available, else store the RSS excerpt directly.

    Pass 2 — summarised_by = 'rss' in last 48 h (Ollama only):
              Upgrade rough RSS excerpts to proper AI summaries now that
              Ollama is running.

    Returns total number of articles summarised / upgraded.
    """
    use_ai = _ollama_available()
    log.info(
        "Summariser: Ollama %s",
        "available — generating AI summaries" if use_ai else "offline — RSS excerpt fallback",
    )

    conn = get_connection()
    try:
        with conn.cursor() as cur:

            # Pass 1 — never summarised
            cur.execute("""
                SELECT id, title, source, rss_excerpt
                FROM   articles
                WHERE  summary IS NULL
                  AND  published_at > NOW() - INTERVAL '48 hours'
                ORDER  BY published_at DESC
                LIMIT  %s
            """, (limit,))
            unsummarised = cur.fetchall()

            # Pass 2 — upgrade RSS fallbacks (AI only)
            rss_rows = []
            if use_ai:
                cur.execute("""
                    SELECT id, title, source, rss_excerpt
                    FROM   articles
                    WHERE  summarised_by = 'rss'
                      AND  published_at > NOW() - INTERVAL '48 hours'
                    ORDER  BY published_at DESC
                    LIMIT  %s
                """, (limit,))
                rss_rows = cur.fetchall()

        rows = list(unsummarised) + list(rss_rows)

        if not rows:
            log.info("Summariser: nothing to process.")
            return 0

        log.info(
            "Summariser: %d articles (%d new, %d RSS upgrades)...",
            len(rows), len(unsummarised), len(rss_rows),
        )

        count = 0

        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    excerpt = row["rss_excerpt"] or ""

                    if use_ai:
                        summary = _ollama_summarise(row["title"], row["source"], excerpt)
                        method  = "ai"
                    else:
                        # Fallback: use the RSS excerpt as-is if it's substantial
                        summary = excerpt.strip() if len(excerpt.strip()) > 60 else None
                        method  = "rss"

                    if not summary:
                        log.debug("  No summary for: %s", row["title"][:60])
                        continue

                    cur.execute(
                        """
                        UPDATE articles
                           SET summary       = %s,
                               summarised_by = %s
                         WHERE id = %s
                        """,
                        (summary, method, row["id"]),
                    )
                    count += 1
                    log.debug(
                        "  [%s] %s",
                        method.upper(),
                        row["title"][:70],
                    )

                    if use_ai:
                        time.sleep(0.1)

        log.info("Summariser: %d articles processed.", count)
        return count
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    summarise_articles()
