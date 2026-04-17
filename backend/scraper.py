"""
Veris — RSS ingestion pipeline.
Sources are defined in sources.py; scoring is handled by craap.py.
Run manually or via GitHub Actions every 5 hours.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta

import feedparser
import psycopg2
import requests
from db import get_connection, init_db
from sources import SOURCES
from craap import score_article
from ranker import rank_unranked_articles
from summariser import summarise_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

CUTOFF_HOURS = 24

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Veris/1.0; "
        "+https://github.com/your-org/veris)"
    )
}

# Source suffixes appended by Google News RSS — strip before storing/hashing
# so "Ukraine talks - AP News" and "Ukraine talks" are treated as the same article.
_SOURCE_SUFFIXES = (
    " - AP News", " - The Associated Press",
    " - BBC News", " - BBC",
    " | AFP", " - AFP", " - Agence France-Presse",
    " - NPR", " - NPR News",
    " - DW", " - Deutsche Welle",
    " - NHK", " - NHK World News", " - NHK WORLD-JAPAN",
    " - ABC News", " - ABC",           # Australian ABC
    " - CBC News", " - CBC",
    " - RFI", " - Radio France Internationale",
    " - PBS NewsHour", " - PBS",
    " | Reuters", " - Reuters",        # in case Reuters leaks through
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_title(title: str) -> str:
    """Strip Google News source suffixes and normalise whitespace."""
    t = title.strip()
    for suffix in _SOURCE_SUFFIXES:
        if t.endswith(suffix):
            t = t[: -len(suffix)].strip()
            break   # only strip one suffix
    return t


def _title_hash(title: str) -> str:
    """Hash the *cleaned* title so near-identical titles dedup correctly."""
    return hashlib.sha256(_clean_title(title).lower().encode()).hexdigest()


def _resolve_url(entry, raw_url: str) -> str | None:
    """
    Return a real, working article URL.

    Strategy (cheapest first):
      1. feedparser's entry.source.href — free, no HTTP round-trip.
      2. Follow HTTP redirects for news.google.com URLs.
      3. Trust direct URLs from official feeds as-is.

    Returns None if the URL cannot be resolved to a real article page
    (e.g. the redirect stays on google.com, or the request fails).
    """
    # 1 — feedparser sometimes gives the canonical URL in entry.source.href
    try:
        src = getattr(entry, "source", None)
        href = ""
        if isinstance(src, dict):
            href = src.get("href", "").strip()
        elif hasattr(src, "href"):
            href = (src.href or "").strip()
        if href and href.startswith("http") and "news.google.com" not in href:
            return href
    except Exception:
        pass

    # 2 — Google News redirect — follow it
    if "news.google.com" in raw_url:
        try:
            resp = requests.get(
                raw_url,
                allow_redirects=True,
                timeout=8,
                headers={**REQUEST_HEADERS, "Accept": "text/html,*/*"},
                stream=True,   # don't download body
            )
            resp.close()
            final = resp.url
            if "news.google.com" not in final and resp.status_code < 400:
                return final
            log.debug("  URL stayed on google.com or bad status — dropping: %s", raw_url[:80])
            return None
        except Exception as exc:
            log.debug("  URL resolution failed (%s) — dropping: %s", exc, raw_url[:80])
            return None

    # 3 — Already a direct URL — trust it
    return raw_url


def _strip_html(text: str) -> str:
    """Remove HTML tags and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_excerpt(entry) -> str:
    """
    Pull the best available text excerpt from an RSS entry.

    Priority:
      1. entry.content[0].value  — some outlets (DW, RFI, NPR) publish
                                   the full article body here
      2. entry.summary           — the standard RSS description/excerpt
      3. ""                      — nothing available

    HTML is stripped. Result is capped at 3000 chars so Ollama stays fast.
    """
    # 1 — full content block (Atom / RSS2 with content:encoded)
    content_list = getattr(entry, "content", None)
    if content_list and isinstance(content_list, list):
        raw = content_list[0].get("value", "") if isinstance(content_list[0], dict) \
              else getattr(content_list[0], "value", "")
        if raw:
            text = _strip_html(raw)
            if len(text) > 100:
                return text[:3000]

    # 2 — standard summary / description
    raw = getattr(entry, "summary", "") or ""
    if raw:
        return _strip_html(raw)[:3000]

    return ""


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field, None)
        if value:
            try:
                return datetime(*value[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _is_fresh(published_at: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=CUTOFF_HOURS)
    return published_at >= cutoff


# ---------------------------------------------------------------------------
# Core ingestion
# ---------------------------------------------------------------------------

def fetch_feed(source_cfg: dict, feed_url: str) -> list[dict]:
    """Download one RSS feed; score each entry; return passing articles."""
    source_name = source_cfg["name"]
    log.info("Fetching %-6s — %s", source_name, feed_url)

    parsed = feedparser.parse(feed_url, request_headers=REQUEST_HEADERS)

    http_status = getattr(parsed, "status", None)
    if http_status and http_status not in (200, 301, 302):
        log.warning("  Feed returned HTTP %s — skipping", http_status)
        return []
    if parsed.bozo:
        log.warning("  Feed parse warning: %s", parsed.bozo_exception)

    articles = []
    rejected = 0

    for entry in parsed.entries:
        raw_title = getattr(entry, "title", "").strip()
        raw_url   = getattr(entry, "link",  "").strip()
        if not raw_title or not raw_url:
            continue

        # Resolve Google News redirects → real article URL; skip if unresolvable
        url = _resolve_url(entry, raw_url)
        if not url:
            rejected += 1
            continue

        # Strip source suffixes BEFORE scoring and storing
        title = _clean_title(raw_title)

        published_at = _parse_date(entry) or datetime.now(timezone.utc)

        if not _is_fresh(published_at):
            continue

        rss_excerpt = _extract_excerpt(entry)

        craap = score_article(
            title=title,
            url=url,
            source_name=source_name,
            published_at=published_at,
            excerpt=rss_excerpt,
        )

        if not craap["passes"]:
            log.debug(
                "  REJECT (score %d/30) — %s",
                craap["total"], title[:60]
            )
            rejected += 1
            continue

        articles.append({
            "title":        title,
            "source":       source_name,
            "published_at": published_at,
            "url":          url,
            "craap_score":  craap["total"],
            "title_hash":   _title_hash(title),
            "rss_excerpt":  rss_excerpt,
        })

    log.info(
        "  → %d accepted, %d rejected by CRAAPO filter",
        len(articles), rejected
    )
    return articles


def upsert_articles(articles: list[dict]) -> int:
    if not articles:
        return 0

    inserted = 0
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT url FROM articles WHERE created_at > NOW() - INTERVAL '25 hours'"
                )
                existing_urls = {row["url"] for row in cur.fetchall()}
                seen_hashes: set[str] = set()

                for art in articles:
                    if art["url"] in existing_urls:
                        continue
                    if art["title_hash"] in seen_hashes:
                        continue
                    seen_hashes.add(art["title_hash"])

                    try:
                        cur.execute(
                            """
                            INSERT INTO articles
                                (title, source, published_at, url, craap_score, rss_excerpt)
                            VALUES
                                (%(title)s, %(source)s, %(published_at)s, %(url)s,
                                 %(craap_score)s, %(rss_excerpt)s)
                            ON CONFLICT (url) DO NOTHING
                            """,
                            art,
                        )
                        if cur.rowcount:
                            inserted += 1
                            existing_urls.add(art["url"])
                    except psycopg2.Error as exc:
                        log.error("DB error inserting %s: %s", art["url"], exc)
                        conn.rollback()
    finally:
        conn.close()

    return inserted


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
    log.info("=== Veris ingestion started ===")
    init_db()   # ensures all columns exist before any queries run
    all_articles: list[dict] = []

    for source_cfg in SOURCES:
        for feed_url in source_cfg["feeds"]:
            try:
                all_articles.extend(fetch_feed(source_cfg, feed_url))
            except Exception as exc:
                log.error(
                    "Failed to fetch %s feed %s: %s",
                    source_cfg["name"], feed_url, exc
                )

    log.info("Total articles passing CRAAP filter: %d", len(all_articles))
    all_articles.sort(key=lambda a: a["published_at"], reverse=True)

    inserted = upsert_articles(all_articles)
    log.info("=== Ingestion complete — %d new articles inserted ===", inserted)

    # Rank any articles that don't yet have an importance score
    log.info("--- Starting importance ranking ---")
    rank_unranked_articles()

    # Summarise articles so users can read without leaving the app
    log.info("--- Starting summarisation ---")
    summarise_articles()


if __name__ == "__main__":
    run()
