"""
Veris — Curated source registry.

Inclusion criteria (all must pass):
  ✓ Not owned by a political party, PAC, or partisan advocacy group
  ✓ No stated partisan editorial mandate
  ✓ Established, public corrections/editorial policy
  ✓ Funded by public licence fee, international development mandate,
    non-profit cooperative model, or independent trust — NOT by political donors
  ✓ Member of a recognised press council or equivalent accountability body

Sources intentionally excluded:
  - Reuters.com  (paywall — links break UX)
  - Al Jazeera   (Qatari state editorial influence, documented)
  - Any outlet with majority ownership by a political party or ideological PAC
"""

# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------
# TIER 1 — Wire services: purely factual dispatch, no editorial voice
# TIER 2 — International public broadcasters: strong independence statutes,
#           publicly funded, editorially separated from government by law
# ---------------------------------------------------------------------------

SOURCES = [
    # ------------------------------------------------------------------
    # TIER 1 — Wire services
    # ------------------------------------------------------------------
    {
        "name": "AP",
        "domain": "apnews.com",
        "tier": 1,
        "authority_score": 5,     # CRAAPO Authority pre-score
        "purpose_score": 5,       # CRAAPO Purpose pre-score
        "objectivity_score": 5,   # CRAAPO Objectivity: wire service, no editorial stance
        "feeds": [
            "https://news.google.com/rss/search?q=site:apnews.com&hl=en-US&gl=US&ceid=US:en",
            # rsshub.app removed — public instance returns 403
        ],
        "why_included": (
            "Non-profit cooperative owned by US member newspapers. "
            "No editorial stance; dispatches are straight-news only."
        ),
    },
    {
        "name": "AFP",
        "domain": "afp.com",
        "tier": 1,
        "authority_score": 5,
        "purpose_score": 5,
        "objectivity_score": 5,   # wire service, statutory independence (Loi n°57-32)
        "feeds": [
            "https://news.google.com/rss/search?q=site:afp.com&hl=en-US&gl=US&ceid=US:en",
        ],
        "why_included": (
            "French public wire service. Editorially independent from the state "
            "by statute (Loi n°57-32). Global reach, strict separation from government."
        ),
    },

    # ------------------------------------------------------------------
    # TIER 2 — International public broadcasters
    # ------------------------------------------------------------------
    {
        "name": "NPR",
        "domain": "npr.org",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # non-profit, editorial firewall from funders
        "feeds": [
            "https://feeds.npr.org/1001/rss.xml",   # News
            "https://feeds.npr.org/1003/rss.xml",   # U.S.
            "https://feeds.npr.org/1004/rss.xml",   # World
        ],
        "why_included": (
            "US non-profit public radio. Editorial independence protected by "
            "NPR ethics handbook; funding from foundations, not partisan donors."
        ),
    },
    {
        "name": "BBC",
        "domain": "bbc.com",
        "tier": 2,
        "authority_score": 5,
        "purpose_score": 4,
        "objectivity_score": 5,   # Royal Charter + Ofcom regulation — strongest accountability
        "feeds": [
            # feeds.bbci.co.uk no longer resolves; using Google News mirror
            "https://news.google.com/rss/search?q=site:bbc.com/news&hl=en-US&gl=US&ceid=US:en",
        ],
        "why_included": (
            "UK public broadcaster. Royal Charter and Agreement mandate "
            "due impartiality; regulated by Ofcom."
        ),
    },
    {
        "name": "DW",
        "domain": "dw.com",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # DW Act, editorial independence guaranteed by law
        "feeds": [
            "https://rss.dw.com/rdf/rss-en-all",
        ],
        "why_included": (
            "Deutsche Welle, Germany's international public broadcaster. "
            "Governed by the DW Act; editorial independence guaranteed by law."
        ),
    },
    {
        "name": "NHK",
        "domain": "nhk.or.jp",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # Broadcast Act, public mandate
        "feeds": [
            # nhk.or.jp DNS not resolving externally; using Google News mirror
            "https://news.google.com/rss/search?q=site:nhk.or.jp/nhkworld&hl=en-US&gl=US&ceid=US:en",
        ],
        "why_included": (
            "NHK World, Japan's public international broadcaster. "
            "Independent editorial standards; regulated under the Broadcast Act."
        ),
    },
    {
        "name": "ABC",
        "domain": "abc.net.au",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # ABC Act 1983, statutory independence
        "feeds": [
            # abc.net.au DNS not resolving externally; using Google News mirror
            "https://news.google.com/rss/search?q=site:abc.net.au/news&hl=en-US&gl=US&ceid=US:en",
        ],
        "why_included": (
            "Australian Broadcasting Corporation. Statutory independence "
            "under the ABC Act 1983; editorial policies prohibit partisan content."
        ),
    },
    {
        "name": "CBC",
        "domain": "cbc.ca",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # Broadcasting Act, Crown corporation independence
        "feeds": [
            # cbc.ca DNS not resolving externally; using Google News mirror
            "https://news.google.com/rss/search?q=site:cbc.ca/news&hl=en-US&gl=US&ceid=US:en",
        ],
        "why_included": (
            "Canadian Broadcasting Corporation. Crown corporation with editorial "
            "independence protected by the Broadcasting Act."
        ),
    },
    {
        "name": "RFI",
        "domain": "rfi.fr",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # France Médias Monde governance
        "feeds": [
            "https://www.rfi.fr/en/rss",
        ],
        "why_included": (
            "Radio France Internationale. French public international broadcaster; "
            "editorially independent under France Médias Monde governance."
        ),
    },
    {
        "name": "PBS",
        "domain": "pbs.org",
        "tier": 2,
        "authority_score": 4,
        "purpose_score": 4,
        "objectivity_score": 4,   # non-profit, strict funder-editorial firewall
        "feeds": [
            "https://www.pbs.org/newshour/feeds/rss/headlines",
        ],
        "why_included": (
            "PBS NewsHour. Non-profit public TV. Journalism funded by foundations "
            "with strict firewalls between funders and editorial decisions."
        ),
    },
]

# Fast lookups used by the scraper and CRAAP scorer
SOURCE_BY_NAME: dict = {s["name"]: s for s in SOURCES}
ALLOWED_SOURCE_NAMES: set = {s["name"] for s in SOURCES}
