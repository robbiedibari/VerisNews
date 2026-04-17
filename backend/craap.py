"""
Veris — CRAAPO scorer  (v3)

CRAAPO = Currency · Relevance · Authority · Accuracy · Purpose · Objectivity
Each dimension scores 1–5. Total range: 6–30.
Articles below MIN_SCORE are dropped at ingestion.

v3 changes vs v2
─────────────────
• Objectivity (O): NEW 6th dimension — institutional backing, sponsored content
  detection, and quality-control signals inspired by the SIFT framework.
• Relevance:    celebrity content is now a R=1 hard-fail (not just P=2 soft hit).
                _NAMED_ENTITY_RE fixed — months/weekdays removed (they fire on
                everything and add no signal), replaced with concrete geopolitical
                and governmental entities.
• Accuracy:     optionally accepts rss_excerpt; sensational/weasel language in
                the body is a stronger signal than the title alone (SIFT: Trace claims).
• Cross-dimension quality bonus: R≥4 AND Accuracy≥4 → +1 to total (SIFT: Find
  other coverage confirms quality from multiple angles).
• MIN_SCORE:    17 → 20  (same ~67% pass threshold against the new 30-point max).

All rules are deterministic and auditable (no AI, no LLM).
"""

import re
from datetime import datetime, timezone

from sources import SOURCE_BY_NAME

MIN_SCORE = 20   # articles scoring below this are dropped at ingestion (out of 30)


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
# Is this an actual news event — not an opinion, listicle, promo, or celebrity?
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
# SIFT: celebrity / entertainment = not geopolitical news — hard R=1 fail
# Mirrors _PURPOSE_SOFT_RE but here it gates relevance, not just purpose
_CELEB_RELEVANCE_RE = re.compile(
    r"\b(taylor swift|beyonc[eé]|kim kardashian|kanye( west)?|drake|rihanna|"
    r"selena gomez|ariana grande|harry styles|billie eilish|britney spears|"
    r"lady gaga|justin bieber|miley cyrus|dua lipa|the weeknd|post malone|"
    r"grammy (award|winner|nominee)|golden globe|emmy award|"
    r"box office (record|gross)|concert tour|album (chart|release|drop)|"
    r"red carpet|celebrity couple|celebrity split)\b",
    re.IGNORECASE,
)

# Positive signals — specific, verifiable events
# v3: months and weekdays removed — "January report" / "Monday meeting" fire on
# nearly every headline and carry no meaningful relevance signal.
_NAMED_ENTITY_RE = re.compile(
    r"\b(\d{4}|"                                    # 4-digit years (not ordinal lists)
    r"united\s+(states|nations|kingdom|arab|front)|"
    r"president|prime\s+minister|foreign\s+minister|secretary\s+of\s+state|"
    r"parliament|congress|senate|cabinet|"
    r"supreme\s+court|high\s+court|tribunal|"
    r"police|military|army|navy|air\s+force|coast\s+guard|"
    r"nato|un\b|eu\b|who\b|imf\b|wto\b|iaea\b|icj\b|"
    r"government|authorities|officials?|ministry|agency|commission|"
    r"summit|treaty|accord|ceasefire|election|referendum|"
    r"forces|troops|soldiers|hostages?)\b",
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

    # Hard fails
    if _OPINION_RE.search(title):           return 1   # opinion/analysis
    if _LISTICLE_RE.search(title):          return 1   # listicle
    if _PROMO_RE.search(title):             return 1   # promotional
    if _NAV_PAGE_RE.search(title):          return 1   # homepage / audio / video page
    if _CELEB_RELEVANCE_RE.search(title):   return 1   # celebrity/entertainment content

    # Soft penalisations
    if _QUESTION_RE.search(title):          score -= 1  # Betteridge's Law
    if len(title.strip()) < 20:             score -= 1  # too short to be substantive
    if len(title.strip()) > 220:            score -= 1  # likely concatenated/garbled

    non_article = ("/author/", "/tag/", "/topic/", "/category/", "/section/")
    if any(p in url.lower() for p in non_article): score -= 1

    # Positive signals
    if _NAMED_ENTITY_RE.search(title):      score += 1  # specific entity
    if _ACTIVE_VERB_RE.search(title):       score += 1  # concrete event verb

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
# Heuristic checks on title and (optionally) rss_excerpt for quality signals.
# SIFT "Trace claims": sensational/weasel language in the body is a stronger
# signal than the title alone.
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
# Positive accuracy signal — verifiable specific number or quantity
# Require 2+ digit numbers OR a unit suffix — prevents "7 things" listicle
# titles from getting a free accuracy bonus
_SPECIFIC_RE = re.compile(r"\b(\d{2,}[\d,]*|\d+(%|bn|mn|km|kg|°|people|soldiers|votes))\b")

def score_accuracy(title: str, excerpt: str = "") -> int:
    score = 4   # professional outlets get a reasonable baseline

    # Title-level checks
    if title.count("!") >= 2:                    score -= 2
    elif "!" in title:                            score -= 1
    if _QUESTION_RE.search(title):               score -= 1   # speculative
    if _SENSATIONAL_RE.search(title):            score -= 2
    if _SUPERLATIVE_RE.search(title):            score -= 1
    if _WEASEL_RE.search(title):                 score -= 1

    real_caps = [w for w in _CAPS_WORD_RE.findall(title) if w not in _KNOWN_ACRONYMS]
    if len(real_caps) >= 2:                      score -= 1

    # Reward verifiable specifics in title
    if _SPECIFIC_RE.search(title):               score += 1

    # Body-level checks via RSS excerpt (SIFT: Trace claims)
    # Only penalise once per category to avoid double-counting with title hits
    if excerpt:
        body = excerpt[:600]  # first 600 chars — enough for lede paragraph
        if _SENSATIONAL_RE.search(body) and not _SENSATIONAL_RE.search(title):
            score -= 1
        if _WEASEL_RE.search(body) and not _WEASEL_RE.search(title):
            score -= 1
        if body.count("!") >= 3:
            score -= 1

    return max(1, min(5, score))


# ─────────────────────────────────────────────────────────────────────────────
# P — Purpose  (1–5)
# Inferred from title signals — not just the source.
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
    r"quiz|fun fact|did you know|throwback|"
    r"taylor swift|beyonc[eé]|kim kardashian|grammy|oscar award|"
    r"box office|album (release|chart)|concert tour|red carpet)\b",
    re.IGNORECASE,
)
# Geopolitics signal — these topics are the editorial core of Veris
_GEOPOLITICS_RE = re.compile(
    r"\b(war|invasion|coup|sanctions|nato|un security|ceasefire|"
    r"nuclear|missile|troops|airstrike|diplomatic|treaty|summit|"
    r"bilateral|sovereignty|territorial|embargo|blockade|referendum|"
    r"foreign minister|secretary of state|prime minister|"
    r"kremlin|pentagon|whitehouse|g7|g20)\b",
    re.IGNORECASE,
)

def score_purpose(source_name: str, title: str) -> int:
    # Hard overrides based on title content
    if _PURPOSE_OPINION_RE.search(title): return 1
    if _PURPOSE_SOFT_RE.search(title):    return 2

    # Base from source, then modulate
    source = SOURCE_BY_NAME.get(source_name)
    base   = source["purpose_score"] if source else 2

    if _PURPOSE_NEWS_RE.search(title):   base = min(5, base + 1)
    if _GEOPOLITICS_RE.search(title):    base = min(5, base + 1)  # geopolitics boost

    return max(1, min(5, base))


# ─────────────────────────────────────────────────────────────────────────────
# O — Objectivity  (1–5)  NEW in v3
# SIFT "Stop and reflect": does the institution behind this content exercise
# quality control, and does its affiliation bias the information?
#
# Key signals:
#   • Source institutional backing (wire/public-broadcaster → high objectivity)
#   • Sponsored / advertorial / partner-content URL patterns → hard 1
#   • Sponsored title markers → hard 1
#   • Editorial URL path (opinion/blog) softly reduces even good sources
# ─────────────────────────────────────────────────────────────────────────────

_SPONSORED_URL_RE = re.compile(
    r"/(sponsored|advertorial|partner.content|brand.content|"
    r"native.?ad|promoted|paid.content|branded)/",
    re.IGNORECASE,
)
_SPONSORED_TITLE_RE = re.compile(
    r"\b(sponsored|brought to you by|in partnership with|"
    r"paid post|advertorial|presented by|partner content)\b",
    re.IGNORECASE,
)
# State-controlled / propaganda outlets — none are in our source registry,
# but added as defence-in-depth if a title quotes or names them
_PROPAGANDA_RE = re.compile(
    r"\b(cgtn|xinhua|rt\s+news|sputnik|global times|people.s daily|tass)\b",
    re.IGNORECASE,
)

def score_objectivity(source_name: str, title: str, url: str) -> int:
    # Hard fails — sponsored or propaganda content is objectively 1
    if _SPONSORED_URL_RE.search(url):       return 1
    if _SPONSORED_TITLE_RE.search(title):   return 1

    source = SOURCE_BY_NAME.get(source_name)
    if not source:
        return 2  # unknown source — neutral-low, no quality-control evidence

    base = source["objectivity_score"]

    # Editorial URL softly reduces even institutionally strong sources
    # (an opinion piece from BBC is still less objective than a news dispatch)
    if _EDITORIAL_URL_RE.search(url):   base = max(1, base - 1)

    return max(1, min(5, base))


# ─────────────────────────────────────────────────────────────────────────────
# Composite scorer
# ─────────────────────────────────────────────────────────────────────────────

def score_article(
    title: str,
    url: str,
    source_name: str,
    published_at: datetime,
    excerpt: str = "",
) -> dict:
    """
    Returns a dict with per-dimension scores, total, and pass/fail.
    {
        "currency":     int,
        "relevance":    int,
        "authority":    int,
        "accuracy":     int,
        "purpose":      int,
        "objectivity":  int,
        "total":        int,   # max 31 (30 base + quality bonus)
        "passes":       bool,
    }

    Cross-dimension quality bonus (SIFT "Find other coverage"):
    When both Relevance ≥ 4 AND Accuracy ≥ 4, the story has passed
    independent quality checks on two axes — total gets +1.
    """
    c     = score_currency(published_at)
    r     = score_relevance(title, url)
    a_aut = score_authority(source_name, title, url)
    a_acc = score_accuracy(title, excerpt)
    p     = score_purpose(source_name, title)
    o     = score_objectivity(source_name, title, url)

    # Cross-dimension quality bonus
    quality_bonus = 1 if (r >= 4 and a_acc >= 4) else 0

    total = c + r + a_aut + a_acc + p + o + quality_bonus

    # Hard fail conditions — source authority/total must not rescue these:
    #   R=1  → opinion, promo, audio, nav page, listicle, celebrity content
    #   O=1  → sponsored/advertorial/propaganda URL or title marker
    passes = (r > 1) and (o > 1) and (total >= MIN_SCORE)

    return {
        "currency":     c,
        "relevance":    r,
        "authority":    a_aut,
        "accuracy":     a_acc,
        "purpose":      p,
        "objectivity":  o,
        "total":        total,
        "passes":       passes,
    }
