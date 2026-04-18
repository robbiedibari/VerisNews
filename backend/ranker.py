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
import re
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
You are a senior geopolitical news editor. Rate the newsworthiness of the headline below.
Veris focuses on geopolitics, international affairs, war, diplomacy, and major economic events.

Scale:
5 = Breaking  — war declaration/escalation, mass-casualty disaster, assassination, major election result, pandemic
4 = Critical  — major policy shift, large-scale unrest, significant diplomatic development, economic crisis
3 = Important — notable geopolitical development, significant regional event, meaningful policy change
2 = Standard  — routine political statements, minor developments, domestic follow-up stories
1 = Low       — celebrity news, entertainment, soft news, opinion, minor local events

RULES (apply strictly):
- Celebrity / entertainment / sports personalities → never above 2
- Verbal clashes only ("X slams Y", "X hits back") without concrete action → cap at 3
- Fact-checks, analysis, opinion, commentary → cap at 2
- Domestic political gossip or routine statements → cap at 2
- Geopolitical events (war, sanctions, invasions, coups, treaties, summits) → prioritise higher scores

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

# ── Keyword tiers — geopolitics-first ──────────────────────────────────────
# "attack" intentionally excluded: too generic — fires on Taylor Swift concert
# attacks, verbal attacks, cyber attacks in non-critical contexts.

_BREAKING = {
    # Mass-casualty / physical catastrophe
    "killed", "dead", "deaths", "war", "bombing", "explosion", "blast",
    "earthquake", "hurricane", "tsunami", "flood", "wildfire",
    "massacre", "airstrike", "airstrikes", "genocide", "famine",
    "shooting", "stabbing",
    # Geopolitical shocks
    "coup", "assassination", "assassinated", "pandemic", "outbreak",
    "invasion", "invaded", "invades", "nuclear", "ceasefire", "hostage",
    "annexed", "annexation",
}

# "trade war", "price war", "culture war" etc. should NOT trigger Breaking
_SOFT_WAR_RE = re.compile(
    r"\b(trade|price|culture|currency|turf|bidding|cold|cyber)\s+war\b",
    re.IGNORECASE,
)
_CRITICAL = {
    # Elections & governance shocks
    "election", "elected", "referendum", "impeach", "indicted", "arrested",
    # Economic crises / sanctions
    "sanctions", "recession", "embargo", "tariffs", "default", "collapse",
    # Military / diplomatic escalation
    "missile", "troops", "deployed", "military", "summit", "treaty",
    "diplomatic", "sovereignty", "territorial", "blockade",
    # Major crises
    "crisis", "emergency", "ban",
}
_IMPORTANT = {
    # Geopolitical / international
    "foreign", "bilateral", "alliance", "nato", "un", "g7", "g20",
    "pentagon", "kremlin", "whitehouse", "parliament", "congress", "senate",
    # Governance & leadership
    "government", "minister", "president", "prime",
    # Legal / policy
    "investigation", "trial", "verdict", "ruling", "policy", "reform",
    "legislation", "resolution",
    # Economic
    "inflation", "budget", "trade", "agreement", "deal",
    # Environment / humanitarian
    "climate", "migration", "refugee", "humanitarian",
}

# ── Pre-filters that cap the score before keyword matching ──────────────────

# Celebrity names and entertainment — these topics should never reach Breaking
_CELEBRITY_RE = re.compile(
    r"\b(taylor swift|beyonc[eé]|kim kardashian|kanye( west)?|rihanna|"
    r"harry styles|ariana grande|billie eilish|selena gomez|justin bieber|"
    r"lady gaga|katy perry|britney spears|miley cyrus|dua lipa|"
    r"travis kelce|nicki minaj|cardi b|bad bunny|"
    # Profession identifiers — catches unknown/emerging celebrities by role title
    # regardless of fame level. "actor" excluded: "non-state actor" / "bad actor"
    # are legitimate geopolitics terms.
    r"singer|rapper|r&b (singer|artist|star)|pop (singer|artist)|"
    r"actress|influencer|youtuber|tiktok(er| star)?|"
    r"grammy|oscar (award|ceremony|winner)|emmy award|bafta|"
    r"box office|album (release|chart|debut)|concert tour|red carpet|"
    r"celebrity (news|drama|feud)|pop star|reality (tv|show)|"
    r"divorce settlement|baby shower|pregnancy rumou?r|"
    r"engagement ring|paparazzi)\b",
    re.IGNORECASE,
)

# Pure rhetorical political drama — verbal conflict, no concrete consequence
# These cap at Important (3) unless accompanied by a concrete-action word
_RHETORIC_RE = re.compile(
    r"\b(slams?|blasts?|rips?|lambasts?|lashes out|hits back|fires back|"
    r"clashes? with|mocks?|taunts?|feuds? with|rants? at|"
    r"pushes back|doubles down|hits out|takes aim|takes a swipe|"
    r"criticis[ez]s?|denounces?|condemns?|decries?)\b",
    re.IGNORECASE,
)

# Fact-check / analysis framing — should never be Breaking/Critical
_FACTCHECK_RE = re.compile(
    r"\b(fact.?check|fact.?checking|debunking|myth.?bust|"
    r"is it true|what (we|you) know|what to know|"
    r"explainer|analysis|opinion|commentary)\b",
    re.IGNORECASE,
)

# Concrete-action words that redeem a rhetorical headline (e.g. "clashes" +
# "troops" or "sanctions" means real news, not just a verbal spat)
_CONCRETE_ACTION = (
    _BREAKING
    | {"signed", "elected", "arrested", "launched", "approved", "rejected",
       "sentenced", "declared", "deployed", "resigned", "indicted", "bombed",
       "invaded", "collapsed", "evacuated", "sentenced", "sanctions", "troops",
       "missile", "nuclear", "coup", "invaded"}
)


def _heuristic_rank(title: str) -> dict:
    words = set(title.lower().replace("-", " ").split())

    # 1. Celebrity / entertainment content → cap at Standard (2)
    #    Even genuine events at celebrity-themed venues stay at Important at most.
    if _CELEBRITY_RE.search(title):
        if words & _BREAKING:
            return {"score": 3, "level": "Important", "ai": False, "method": "heuristic"}
        return {"score": 2, "level": "Standard",  "ai": False, "method": "heuristic"}

    # 2. Fact-check / analysis framing → Standard (2)
    if _FACTCHECK_RE.search(title):
        return {"score": 2, "level": "Standard", "ai": False, "method": "heuristic"}

    # 3. "Trade war / price war / cold war" — "war" is economic/metaphorical,
    #    not armed conflict.  Remove it from the Breaking trigger for this title.
    effective_breaking = _BREAKING.copy()
    if _SOFT_WAR_RE.search(title):
        effective_breaking.discard("war")

    # 4. Pure rhetorical political drama → cap at Important (3) unless a
    #    concrete high-stakes word is also present.
    if _RHETORIC_RE.search(title):
        if not (words & _CONCRETE_ACTION):
            return {"score": 3, "level": "Important", "ai": False, "method": "heuristic"}

    # 5. Standard keyword tier logic
    if words & effective_breaking:
        return {"score": 5, "level": "Breaking",  "ai": False, "method": "heuristic"}
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

            # --- Pass 2: re-rank heuristic articles ---
            # Always re-rank articles from the last 48 h so that algorithm
            # improvements take effect on the next pipeline run without needing
            # a manual reset.  When Ollama is available, older articles (up to
            # 7 days) are also upgraded to AI scores.
            heuristic_window = "7 days" if use_ai else "48 hours"
            cur.execute(f"""
                SELECT id, title, source
                FROM   articles
                WHERE  ranked_by = 'heuristic'
                  AND  published_at > NOW() - INTERVAL '{heuristic_window}'
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


# Words that are too common/short to be useful topic tokens
_TOPIC_SKIP = {
    "A", "An", "The", "In", "On", "At", "To", "For", "Of", "And", "But",
    "Or", "As", "By", "Is", "It", "Its", "Was", "Are", "Be", "Has", "Had",
    "Not", "Up", "Can", "New", "One", "Two", "How", "Why", "What", "Who",
    "Over", "With", "From", "Into", "That", "This", "They", "After", "Says",
    "Said", "Will", "More", "Out", "Back", "Off", "Us", "UK", "EU",
}


def _topic_tokens(title: str) -> set[str]:
    """
    Extract significant named tokens (likely proper nouns / entities) from a
    headline. Used for topic-diversity enforcement in get_top_stories().
    Returns a set of title-cased words ≥4 chars that are not stopwords.
    """
    tokens = set()
    for word in re.findall(r"\b[A-Za-z]{4,}\b", title):
        if word[0].isupper() and word not in _TOPIC_SKIP:
            tokens.add(word)
    return tokens


def get_top_stories(n: int = 10) -> list[dict]:
    """
    Return the top-n articles from the last 24 h by importance_score.

    Diversity caps applied in order:
      • Source cap  — max 2 articles per outlet (was 3; tighter for variety)
      • Topic cap   — max 2 articles sharing the same prominent named entity
                      (prevents Trump / Gaza / any single figure flooding the feed)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, source, published_at, url,
                       craap_score, importance_score, importance_level, summary
                FROM   articles
                WHERE  published_at > NOW() - INTERVAL '24 hours'
                  AND  importance_score IS NOT NULL
                ORDER  BY importance_score DESC, craap_score DESC, published_at DESC
                LIMIT  150
            """)
            rows = cur.fetchall()

        source_counts: dict[str, int] = {}
        topic_counts:  dict[str, int] = {}
        top: list[dict] = []

        for row in rows:
            src    = row["source"]
            tokens = _topic_tokens(row["title"])

            # Source diversity cap (max 2 per outlet)
            if source_counts.get(src, 0) >= 2:
                continue

            # Topic diversity cap (max 2 articles sharing a named entity)
            if any(topic_counts.get(t, 0) >= 2 for t in tokens):
                continue

            source_counts[src] = source_counts.get(src, 0) + 1
            for t in tokens:
                topic_counts[t] = topic_counts.get(t, 0) + 1

            top.append(dict(row))
            if len(top) >= n:
                break

        return top
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rank_unranked_articles()
