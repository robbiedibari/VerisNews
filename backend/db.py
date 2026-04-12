import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """
    Idempotent schema bootstrap — safe to call on every scraper run.

    Execution order matters:
      1. CREATE TABLE   — only runs if the table is brand new
      2. ALTER TABLE    — adds any missing columns to existing tables
      3. CREATE INDEX   — runs after all columns are guaranteed to exist
    """

    # Step 1 — table skeleton (no indexes yet)
    create_table = """
    CREATE TABLE IF NOT EXISTS articles (
        id               SERIAL PRIMARY KEY,
        title            TEXT NOT NULL,
        source           TEXT NOT NULL,
        published_at     TIMESTAMP NOT NULL,
        url              TEXT UNIQUE NOT NULL,
        content          TEXT,
        craap_score      SMALLINT,
        importance_score SMALLINT,
        importance_level TEXT,
        ranked_by        TEXT,
        created_at       TIMESTAMP DEFAULT NOW()
    );
    """

    # Step 2 — non-destructive column migrations for pre-existing tables
    migrations = [
        "ALTER TABLE articles ADD COLUMN IF NOT EXISTS craap_score      SMALLINT;",
        "ALTER TABLE articles ADD COLUMN IF NOT EXISTS importance_score SMALLINT;",
        "ALTER TABLE articles ADD COLUMN IF NOT EXISTS importance_level TEXT;",
        "ALTER TABLE articles ADD COLUMN IF NOT EXISTS ranked_by        TEXT;",
    ]

    # Step 3 — indexes (safe now because all columns exist)
    create_indexes = """
    CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles (published_at DESC);
    CREATE INDEX IF NOT EXISTS idx_articles_source       ON articles (source);
    CREATE INDEX IF NOT EXISTS idx_articles_craap        ON articles (craap_score DESC);
    CREATE INDEX IF NOT EXISTS idx_articles_importance   ON articles (importance_score DESC);
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(create_table)
                for migration in migrations:
                    cur.execute(migration)
                cur.execute(create_indexes)
        print("Database initialized.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
