"""
fix_urls.py — one-off migration to clean up broken Google News redirect URLs.

For every article whose stored URL is a news.google.com redirect:
  • Try to resolve it to the real article URL.
  • If resolved  → UPDATE the row with the real URL.
  • If unresolvable → DELETE the row (broken link is worse than no link).

Safe to run multiple times (idempotent — only touches google.com URLs).
"""

import logging
import time

import requests
import psycopg2
from db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Veris/1.0; "
        "+https://github.com/your-org/veris)"
    )
}


def resolve_google_url(url: str) -> str | None:
    """Follow the redirect chain; return final URL or None if it fails."""
    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            timeout=8,
            headers={**REQUEST_HEADERS, "Accept": "text/html,*/*"},
            stream=True,
        )
        resp.close()
        final = resp.url
        if "news.google.com" not in final and resp.status_code < 400:
            return final
    except Exception as exc:
        log.debug("  resolution error: %s", exc)
    return None


def run():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, url FROM articles WHERE url LIKE '%news.google.com%'"
            )
            rows = cur.fetchall()

        log.info("Found %d article(s) with Google News redirect URLs.", len(rows))
        if not rows:
            log.info("Nothing to fix — done.")
            return

        updated = deleted = 0

        for row in rows:
            art_id  = row["id"]
            goog_url = row["url"]

            real_url = resolve_google_url(goog_url)

            with conn:
                with conn.cursor() as cur:
                    if real_url:
                        try:
                            cur.execute(
                                "UPDATE articles SET url = %s WHERE id = %s",
                                (real_url, art_id),
                            )
                            log.info("  ✓ UPDATED  id=%-5d  %s", art_id, real_url[:90])
                            updated += 1
                        except psycopg2.errors.UniqueViolation:
                            # Real URL already exists in the table — just drop duplicate
                            conn.rollback()
                            cur.execute("DELETE FROM articles WHERE id = %s", (art_id,))
                            log.info("  ✗ DELETED  id=%-5d  (duplicate real URL)", art_id)
                            deleted += 1
                    else:
                        cur.execute("DELETE FROM articles WHERE id = %s", (art_id,))
                        log.info("  ✗ DELETED  id=%-5d  (unresolvable)", art_id)
                        deleted += 1

            # Be polite — don't hammer Google
            time.sleep(0.3)

        log.info(
            "Done — %d updated, %d deleted out of %d total.",
            updated, deleted, len(rows),
        )
    finally:
        conn.close()


if __name__ == "__main__":
    run()
