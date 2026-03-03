# SPDX-License-Identifier: GPL-3.0-or-later
"""NLZIET API endpoint contracts.

All API contracts in one place so changes to versioning or paths are
easy to track.  Constants are grouped by API version and sorted
alphabetically within each group.

Naming convention
-----------------
    API_V{n}_RESOURCE          – endpoint template (the contract)
    API_V{n}_RESOURCE_PREFIX   – parser match pattern (prefix-match)

The leading-underscore ``_API_BASE_URL`` is an internal building block;
external code should import the versioned ``API_V*_`` constants instead.
"""

_API_BASE_URL = "https://api.nlziet.nl"

# ── v7 ────────────────────────────────────────────────────────────────
API_V7_APPCONFIG = f"{_API_BASE_URL}/v7/appconfig?os=web&origin=app"
API_V7_CONTINUE_WATCHING = f"{_API_BASE_URL}/v7/continueWatching"

# ── v8 ────────────────────────────────────────────────────────────────
API_V8_PROFILE = f"{_API_BASE_URL}/v8/profile"
API_V8_RECOMMEND = f"{_API_BASE_URL}/v8/recommend/"
API_V8_SERIES = f"{_API_BASE_URL}/v8/series/{{}}"
API_V8_SERIES_PREFIX = f"{_API_BASE_URL}/v8/series/"
API_V8_TRACKED_SERIES = f"{_API_BASE_URL}/v8/trackedseries"

# ── v9 ────────────────────────────────────────────────────────────────
API_V9_CONTINUE_WATCHING = f"{_API_BASE_URL}/v9/continueWatching"

API_V9_EPG = f"{_API_BASE_URL}/v9/epg"
API_V9_EPG_ITEM_DETAIL = f"{_API_BASE_URL}/v9/item/detail/{{}}/{{}}"
API_V9_EPG_LIVE_CHANNEL = f"{_API_BASE_URL}/v9/epg/programlocations/live?channel={{}}"
API_V9_EPG_DATE = f"{_API_BASE_URL}/v9/epg/programlocations?date={{}}"
API_V9_EPG_LIVE = f"{_API_BASE_URL}/v9/epg/programlocations/live"

API_V9_PLACEMENT_EXPLORE_PREFIX = f"{_API_BASE_URL}/v9/placement/rows/explore-"
API_V9_PLACEMENT = f"{_API_BASE_URL}/v9/placement/rows/{{}}"

API_V9_RECOMMEND_WITH = f"{_API_BASE_URL}/v9/recommend/with"
API_V9_RECOMMEND_FILTERED = f"{_API_BASE_URL}/v9/recommend/filtered"

API_V9_SEARCH = (
    f"{_API_BASE_URL}/v9/search"
    "?searchTerm=%s"
    "&limit=100"
    "&offset=0"
    "&contentType=Movie"
    "&contentType=Series"
)
API_V9_SEARCH_PREFIX = f"{_API_BASE_URL}/v9/search?"

API_V9_SEASON_ALL_EPISODES = (
    f"{_API_BASE_URL}/v9/series/{{}}/episodes"
    "?seasonId={}"
    "&limit=400"
)
API_V9_SERIES_EPISODES = (
    f"{_API_BASE_URL}/v9/series/{{}}/episodes"
    "?limit=100"
    "&offset=0"
)
API_V9_SERIES_PLAY = f"{_API_BASE_URL}/v9/series/{{}}/play"
API_V9_SERIES_PREFIX = f"{_API_BASE_URL}/v9/series/"
API_V9_SERIES_SEASON_EPISODES = (
    f"{_API_BASE_URL}/v9/series/{{}}/episodes"
    "?seasonId={}"
    "&limit=100"
    "&offset=0"
)

API_V9_STREAM_HANDSHAKE = f"{_API_BASE_URL}/v9/stream/handshake"
API_V9_LIVE_HANDSHAKE = (
    f"{_API_BASE_URL}/v9/stream/handshake"
    "?context=Live"
    "&channel={}"
    "&drmType=Widevine"
    "&sourceType=Dash"
    "&playerName=BitmovinWeb"
    "&offsetType=Live"
)
API_V9_VOD_HANDSHAKE = (
    f"{_API_BASE_URL}/v9/stream/handshake"
    "?context=OnDemand"
    "&id={}"
    "&drmType=Widevine"
    "&sourceType=Dash"
    "&playerName=BitmovinWeb"
)

API_V9_TRACKED_SERIES = f"{_API_BASE_URL}/v9/trackedseries"
API_V9_WATCH_IN_ADVANCE = f"{_API_BASE_URL}/v9/watchinadvance"

# ── appconfig cache (stored in LocalSettings) ─────────────────────────
APPCONFIG_CACHE_KEY = "nlziet_appconfig"
APPCONFIG_CACHE_TTL = 300          # seconds (matches server epgCacheTime default)

# ── EPG enrichment cache / queue keys (stored in LocalSettings) ───────
EPG_DETAIL_CACHE_KEY = "nlziet_epg_detail_cache"
EPG_ENRICH_QUEUE_KEY = "nlziet_epg_enrich_queue"
EPG_PROGLOC_CACHE_KEY = "nlziet_epg_progloc_cache"
EPG_BACKOFF_CYCLES_KEY = "nlziet_epg_backoff_cycles"
EPG_ENRICH_BATCH_SIZE = 10
EPG_CACHE_TTL_DAYS = 3
EPG_SIGNAL_FILE_NAME = "nlziet_epg_signal_at"   # plain file in addon-data dir
