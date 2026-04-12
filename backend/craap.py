"""
Veris — CRAAP scorer  (v2)

CRAAP = Currency · Relevance · Authority · Accuracy · Purpose
Each dimension scores 1–5. Total range: 5–25.
Articles below MIN_SCORE are dropped at ingestion.

v2 changes vs v1
─────────────────
• Currency:   sharper time-decay — 8h+ articles lose meaningful points
• Relevance:  penalises opinion / analysis / listicle framing;
              rewards named-entity + active-event titles
• Authority:  source tier is the BASE only; editorial markers
              (Opinion:, Analysis:, "Why X is…") cut the score
• Accuracy:   adds Betteridge's Law (question headlines),
              superlatives, weasel words; rewards verifiable specifics
• Purpose:    inferred from title patterns — not from source alone.
              Straight-news verbs → 5; opinion markers → 1–2.

All rules are deterministic and auditable (no AI, no LLM).
"""

import re
from datetime import datetime, timezone

from sources import SOURCE_BY_NAME

MIN_SCORE = 17   # articles scoring below this are dropped at ingestion


# ─────────────────────────────────────────────────────────────────────────────
# C — Currency  (1–5)
# Sharper decay: news older than 8 h starts losing real value.
# ─────────────────────────────────────────────────────────────────────────────

def score_currency(published_at: datetime) -> int:
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_h = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600

    if age_h <  1:  return 5   # breaking / live
    if age_h <  3:  return 4   # very fresh
    if age_h <  8:  return 3   # same-day news
    if age_h < 16:  return 2   # ageing
    if age_h <= 24: return 1   # approaching cutoff
    return 0                   # beyond window (already filtered upstream)


# ─────────────────────────────────────────────────────────────────────────────
# R — Relevance  (1–5)
# Is this an actual news event — not an opinion, listicle, or promo?
# ─────────────────────────────────────────────────────────────────────────────

# Strong signals that the piece is NOT straight news
_OPINION_RE = re.compile(
    r"^(opinion|analysis|comment|commentary|editorial|op-ed|perspective|"
    r"review|explainer|fact.?check|in depth|long.?read|special report)\b"
    r"|\bopinion\b.*:",
    re.IGNORECASE,
)
_LISTICLE_RE  = re.compile(r"^\d+\s+(things|ways|reasons|tips|facts|questions)", re.IGNORECASE)
_QUESTION_RE  = re.compile(r"\?\s*$")
_PROMO_RE     = re.compile(
    r"\b(subscribe|newsletter|sign.?up|podcast|listen now|watch live|"
    r"photo.?gallery|in pictures|sponsored)\b",
    re.IGNORECASE,
)
# Navigation / homepage titles that slip through RSS feeds
_NAV_PAGE_RE  = re.compile(
    r"(breaking news\s*\|.*today|latest news today|top stories|"
    r"^audio\s*:|^video\s*:|^live\s*:|^watch\s*:|^gallery\s*:|"
    r"^(ap|bbc|afp|npr|dw|nhk|abc|cbc|rfi|pbs)\s+(news|world)?\s*[-–]\s*"
    r"(home|breaking|latest|top|live))",
    re.IGNORECASE,
)

# Positive signals — specific, verifiable events
_NAMED_ENTITY_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|\d{4}|united\s+\w+|president|minister|parliament|"
    r"court|police|army|nato|un\b|eu\b|who\b|imf\b)\b",
    re.IGNORECASE,
)
_ACTIVE_VERB_RE = re.compile(
    r"\b(killed|died|signed|approved|rejected|elected|arrested|launched|"
    r"announced|confirmed|denied|ordered|sentenced|agreed|collapsed|"
    r"resigned|fired|deployed|invaded|evacuated|declared|passed|failed|"
    r"wins|loses|strikes|bans|cuts|raises|drops|hits|reaches)\b",
    re.IGNORECASE,
)

def score_relevance(title: str, url: str) -> int:
    score = 3   # neutral starting point (not 5)

    # Hard penalisations
    if _OPINION_RE.search(title):      return 1   # opinion/analysis → hard floor
    if _LISTICLE_RE.search(title):     return 1   # listicle → hard floor
    if _PROMO_RE.search(title):        return 1   # promotional → not news
    if _NAV_PAGE_RE.search(title):     return 1   # homepage / audio / video page

    # Soft penalisations
    if _QUESTION_RE.search(title):     score -= 1  # Betteridge's Law
    if len(title.strip()) < 20:        score -= 1  # too short to be substantive
    if len(title.strip()) > 220:       score -= 1  # likely concatenated/garbled

    non_article = ("/author/", "/tag/", "/topic/", "/category/", "/section/")
    if any(p in url.lower() for p in non_article): score -= 1

    # Positive signals
    if _NAMED_ENTITY_RE.search(title): score += 1  # specific entity
    if _ACTIVE_VERB_RE.search(title):  score += 1  # concrete event verb

    return max(1, min(5, score))


# ─────────────────────────────────────────────────────────────────────────────
# A — Authority  (1–5)
# Source tier is only the BASE. Editorial framing cuts the score.
# ─────────────────────────────────────────────────────────────────────────────

_EDITORIAL_TITLE_RE = re.compile(
    r"^(opinion|analysis|comment|commentary|editorial|op-ed|why|how\s+to|"
    r"what\s+(you|we)|should\s+we|is\s+it\s+time)\b",
    re.IGNORECASE,
)
_EDITORIAL_URL_RE = re.compile(
    r"/(opinion|analysis|commentary|editorial|perspective|blogs?)/",
    re.IGNORECASE,
)

def score_authority(source_name: str, title: str, url: str) -> int:
    source = SOURCE_BY_NAME.get(source_name)
    base   = source["authority_score"] if source else 1

    if _EDITORIAL_TITLE_RE.search(title): base -= 2
    if _EDITORIAL_URL_RE.search(url):     base -= 2

    return max(1, base)


# ─────────────────────────────────────────────────────────────────────────────
# A — Accuracy  (1–5)
# Heuristic checks on the title for quality / reliability signals.
# ─────────────────────────────────────────────────────────────────────────────

_SENSATIONAL_RE = re.compile(
    r"\b(shocking|bombshell|explosive|stunning|unbelievable|outrage|"
    r"scandalous|you won.t believe|mind.blowing|jaw.dropping|goes viral|"
    r"breaks the internet|secret revealed|exposed|obliterated|destroyed|"
    r"crushed|slammed|obliterates|nukes)\b",
    re.IGNORECASE,
)
_SUPERLATIVE_RE  = re.compile(
    r"\b(worst ever|best ever|most (ever|in history)|biggest (ever|in history)|"
    r"all.time (high|low|record))\b",
    re.IGNORECASE,
)
_WEASEL_RE = re.compile(
    r"\b(reportedly|rumoured|alleged|sources say|insiders say|some say|"
    r"could be|may be|might be)\b",
    re.IGNORECASE,
)
_CAPS_WORD_RE    = re.compile(r"\b[A-Z]{4,}\b")
_KNOWN_ACRONYMS  = {
    "NATO","OPEC","UNICEF","NASA","POTUS","SCOTUS","LGBTQ","COVID",
    "FEMA","IAEA","FIFA","OECD","UNHCR","WTO","IAEA","SWIFT","ISIL",
    "ISIS","ASEAN","BRICS","UK","US","EU","UN","AU","AFP","BBC","NPR",
}
# Positive accuracy signal — verifiable specific
# Require 2+ digit numbers OR a unit suffix — prevents "7 things" listicle
# titles from getting a free accuracy bonus
_SPECIFIC_RE = re.compile(r"\b(\d{2,}[\d,]*|\d+(%|bn|mn|km|kg|°|people|soldiers|votes))\b")

def score_accuracy(title: str) -> int:
    score = 4   # professional outlets get a reasonable baseline

    if title.count("!") >= 2:                    score -= 2
    elif "!" in title:                            score -= 1
    if _QUESTION_RE.search(title):                score -= 1   # speculative
    if _SENSATIONAL_RE.search(title):             score -= 2
    if _SUPERLATIVE_RE.search(title):             score -= 1
    if _WEASEL_RE.search(title):                  score -= 1

    real_caps = [w for w in _CAPS_WORD_RE.findall(title) if w not in _KNOWN_ACRONYMS]
    if len(real_caps) >= 2:                       score -= 1

    # Reward verifiable specifics
    if _SPECIFIC_RE.search(title):                score += 1

    return max(1, min(5, score))


# ─────────────────────────────────────────────────────────────────────────────
# P — Purpose  (1–5)
# Inferred from title signals — not just the source.
# A wire service CAN publish opinion; a public broadcaster CAN sponsor content.
# ─────────────────────────────────────────────────────────────────────────────

_PURPOSE_NEWS_RE = re.compile(
    r"\b(killed|signed|elected|arrested|announced|confirmed|launched|"
    r"approved|rejected|sentenced|collapsed|resigned|deployed|declared|"
    r"passed|strikes|bans|wins|loses)\b",
    re.IGNORECASE,
)
_PURPOSE_OPINION_RE = re.compile(
    r"^(opinion|commentary|op.ed|editorial|why\s|how\s+(we|you|to)|"
    r"should\s|what\s+(we|you)\s+need|the\s+case\s+(for|against))\b",
    re.IGNORECASE,
)
_PURPOSE_SOFT_RE = re.compile(
    r"\b(recipe|travel|lifestyle|fashion|celebrity|horoscope|"
    r"quiz|fun fact|did you know|throwback)\b",
    re.IGNORECASE,
)

def score_purpose(source_name: str, title: str) -> int:
    # Hard overrides based on title content
    if _PURPOSE_OPINION_RE.search(title): return 1
    if _PURPOSE_SOFT_RE.search(title):    return 2

    # Base from source, then modulate
    source = SOURCE_BY_NAME.get(source_name)
    base   = source["purpose_score"] if source else 2

    if _PURPOSE_NEWS_RE.search(title):    base = min(5, base + 1)

    return max(1, min(5, base))


# ─────────────────────────────────────────────────────────────────────────────
# Composite scorer
# ─────────────────────────────────────────────────────────────────────────────

def score_article(
    title: str,
    url: str,
    source_name: str,
    published_at: datetime,
) -> dict:
    """
    Returns a dict with per-dimension scores, total, and pass/fail.
    {
        "currency":  int,
        "relevance": int,
        "authority": int,
        "accuracy":  int,
        "purpose":   int,
        "total":     int,
        "passes":    bool,
    }
    """
    c     = score_currency(published_at)
    r     = score_relevance(title, url)
    a_aut = score_authority(source_name, title, url)
    a_acc = score_accuracy(title)
    p     = score_purpose(source_name, title)
    total = c + r + a_aut + a_acc + p

    # Hard fail: R=1 means definitively not a news article (opinion, promo,
    # audio, nav page, listicle). Source authority must not rescue it.
    passes = (r > 1) and (total >= MIN_SCORE)

    return {
        "currency":  c,
        "relevance": r,
        "authority": a_aut,
        "accuracy":  a_acc,
        "purpose":   p,
        "total":     total,
        "passes":    passes,
    }
