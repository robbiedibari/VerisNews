"""
Veris — Article Summariser  (v2 — Gemini Flash)

Generates a 3–4 sentence plain-English summary for each article covering:
  • What happened (the concrete event)
  • Who is involved (countries, leaders, organisations)
  • Why it matters geopolitically
  • One line of context to make sense of it

Primary:  Gemini 1.5 Flash — fast, free tier more than covers our volume
          (1M tokens/day free; we use ~17% of that at current ingestion rate)
Fallback: RSS excerpt stored at scrape time — used automatically when
          GEMINI_API_KEY is not set or the API call fails.

Two passes per pipeline run:
  Pass 1 — articles with summary IS NULL (never summarised)
  Pass 2 — articles summarised_by = 'rss' in last 48 h
            upgraded to proper Gemini summary on next run
"""

import logging
import os
import time

from db import get_connection

log = logging.getLogger(__name__)

_MODEL_NAME = "gemini-1.5-flash"

_PROMPT = """\
You are a news summariser for Veris, a geopolitics-focused news aggregator.

Write a factual summary of this news article in 3-4 sentences.

Rules:
- Sentence 1: state the main event clearly (what happened, where, when)
- Sentence 2: who is involved — specific names, countries, organisations
- Sentence 3: why this matters geopolitically — consequences, implications
- Sentence 4 (optional): one sentence of context that helps understand the story
- Use specific numbers, names, and dates when available in the excerpt
- No opinion, no editorialising, no value judgements
- Do not start with "The article...", "According to...", or "This article..."
- Write in plain, direct English — as if briefing a busy analyst
- If the excerpt is too thin, write what you can from the headline alone

Headline: {title}
Source: {source}
Excerpt: {excerpt}

Write ONLY the summary, no preamble, no labels:"""


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------

def _get_gemini_model():
    """Initialise Gemini client. Returns model or None if key not set."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name=_MODEL_NAME,
            generation_config={
                "temperature":     0.2,   # factual, low creativity
                "max_output_tokens": 300, # ~3-4 sentences
            },
        )
    except Exception as e:
        log.warning("Gemini init failed: %s", e)
        return None


def _gemini_summarise(model, title: str, source: str, excerpt: str) -> str | None:
    prompt = _PROMPT.format(
        title=title,
        source=source,
        excerpt=excerpt[:2000] if excerpt else "(no excerpt available)",
    )
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Sanity check — reject empty or suspiciously short outputs
        if len(text) > 60:
            return text
    except Exception as e:
        log.debug("Gemini summarise error: %s", e)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarise_articles(limit: int = 100) -> int:
    """
    Summarise articles that don't yet have a proper summary.

    Pass 1 — summary IS NULL (never summarised):
              Use Gemini if available, else store the RSS excerpt directly.

    Pass 2 — summarised_by = 'rss' in last 48 h:
              Upgrade rough RSS excerpts to proper Gemini summaries.

    Returns total number of articles summarised / upgraded.
    """
    model = _get_gemini_model()
    use_ai = model is not None

    log.info(
        "Summariser: Gemini %s",
        "available — generating AI summaries" if use_ai else "unavailable — RSS excerpt fallback",
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

            # Pass 2 — upgrade RSS fallbacks to AI summaries
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
            "Summariser: %d articles to process (%d new, %d RSS upgrades)...",
            len(rows), len(unsummarised), len(rss_rows),
        )

        count = 0

        with conn:
            with conn.cursor() as cur:
                for row in rows:
                    excerpt = row["rss_excerpt"] or ""

                    if use_ai:
                        summary = _gemini_summarise(model, row["title"], row["source"], excerpt)
                        method  = "gemini"
                    else:
                        # Fallback: use RSS excerpt if it's substantial enough
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
                    log.debug("  [%s] %s", method.upper(), row["title"][:70])

                    # Respect Gemini free tier: 15 req/min → 1 req per 4s is safe
                    if use_ai:
                        time.sleep(4)

        log.info("Summariser: %d articles processed.", count)
        return count

    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    summarise_articles()
