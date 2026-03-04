# SPDX-License-Identifier: GPL-3.0-or-later
"""NLZIET EPG description/genre enrichment helpers.

These are module-level (stateless) functions so they can be called from both
the channel (``chn_nlziet.py``) and the background service (``retroservice.py``)
without instantiating a full Channel object.

Detail cache format (stored in LocalSettings under ``EPG_DETAIL_CACHE_KEY``):
    {contentItemId: {"description": str|None,
                     "genre":       str|None,
                     "fetched_at":  float}}

Programme-location cache (``nlziet_epg_progloc.json`` in the addon data dir):
    {"fetched_at": float,
     date_str:     [[contentItemId, assetId, start_ts, stop_ts, channel_id,
                     start_at, end_at, title, landscape_url, is_movie,
                     is_replay], ...], ...}

The enrichment queue is ephemeral — built and drained within each
``create_iptv_epg`` call and never written to disk.
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple

from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler

from api import (
    API_V9_EPG_ITEM_DETAIL,
    EPG_BACKOFF_CYCLES_KEY,
    EPG_CACHE_TTL_DAYS,
    EPG_DETAIL_CACHE_KEY,
    EPG_ENRICH_BATCH_SIZE,
    EPG_PROGLOC_CACHE_TTL,
)

# File name for the large progloc cache stored as a plain JSON file (not in
# LocalSettings, which has a practical size limit the progloc cache easily exceeds).
_PROGLOC_CACHE_FILE = "nlziet_epg_progloc.json"

# Overrideable in unit tests: set to a tempdir path to avoid touching the real
# Kodi addon data directory.
_CACHE_DIR = None  # type: Optional[str]

# Type alias for a queue entry
_QueueEntry = List  # [contentItemId, assetId, start_ts, is_now_int]

# Maximum consecutive empty cycles before hitting max backoff
_MAX_BACKOFF_CYCLES = 20


def _get_cache_file(name: str) -> str:
    """Return the full path to a named cache file in the addon data directory.

    When ``_CACHE_DIR`` is set (unit tests), that directory is used instead of
    the real Kodi addon profile path.

    :param str name: File name (no path components).
    :rtype: str
    """
    if _CACHE_DIR is not None:
        return os.path.join(_CACHE_DIR, name)
    import xbmcvfs  # noqa: PLC0415
    import xbmcaddon  # noqa: PLC0415
    profile = xbmcvfs.translatePath(
        xbmcaddon.Addon("plugin.video.retrospect").getAddonInfo("profile")
    )
    return os.path.join(profile, name)


def load_detail_cache() -> Dict[str, dict]:
    """Load the EPG detail cache from LocalSettings.

    :return: Dict mapping contentItemId → {description, genre, fetched_at}.
    :rtype: dict
    """
    raw = AddonSettings.get_setting(EPG_DETAIL_CACHE_KEY, store=LOCAL) or ""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        Logger.warning("NLZIET EPG: Could not parse detail cache, resetting")
        return {}


def save_detail_cache(cache: Dict[str, dict]) -> None:
    """Prune stale entries and save the cache to LocalSettings.

    :param dict cache: The cache dict to persist.
    """
    cutoff = time.time() - EPG_CACHE_TTL_DAYS * 86400
    pruned = {k: v for k, v in cache.items() if v.get("fetched_at", 0) >= cutoff}
    if len(pruned) != len(cache):
        Logger.debug("NLZIET EPG: Pruned %d stale cache entries", len(cache) - len(pruned))
    AddonSettings.set_setting(EPG_DETAIL_CACHE_KEY, json.dumps(pruned), store=LOCAL)


def load_progloc_cache() -> Tuple[Dict, bool]:
    """Load the programme-location cache from its JSON cache file.

    :return: Tuple of (cache_dict, is_stale).  ``is_stale`` is True when the
             cache was absent or older than ``EPG_PROGLOC_CACHE_TTL`` seconds
             (caller should re-fetch and treat the cycle as "interesting").
    :rtype: tuple
    """
    path = _get_cache_file(_PROGLOC_CACHE_FILE)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, IOError):
        Logger.debug("NLZIET EPG: progloc cache absent")
        return {}, True
    except (ValueError, TypeError):
        Logger.warning("NLZIET EPG: Could not parse progloc cache, resetting")
        return {}, True
    fetched_at = data.get("fetched_at", 0)
    age = time.time() - fetched_at
    is_stale = age > EPG_PROGLOC_CACHE_TTL
    date_keys = sum(1 for k in data if k != "fetched_at" and k != "subscribed_channels")
    if is_stale:
        Logger.debug("NLZIET EPG: progloc cache stale (age=%.0fs, %d date keys)", age, date_keys)
    else:
        Logger.debug("NLZIET EPG: progloc cache hit (age=%.0fs, %d date keys)", age, date_keys)
    return data, is_stale


def save_progloc_cache(cache: Dict) -> None:
    """Persist the programme-location cache to its JSON cache file.

    :param dict cache: Dict of {date_str: [[cid, assetId, ...], ...]}
                       plus a top-level ``"fetched_at"`` key.
    """
    path = _get_cache_file(_PROGLOC_CACHE_FILE)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cache, fh)
    except (OSError, IOError) as exc:
        Logger.warning("NLZIET EPG: Could not save progloc cache: %s", exc)


def load_backoff_cycles() -> int:
    """Return the current consecutive-empty-cycle counter (0 = not backed off).

    :rtype: int
    """
    raw = AddonSettings.get_setting(EPG_BACKOFF_CYCLES_KEY, store=LOCAL) or "0"
    try:
        return max(0, int(raw))
    except (ValueError, TypeError):
        return 0


def save_backoff_cycles(n: int) -> None:
    """Persist the backoff cycle counter.

    :param int n: Counter value (will be clamped to [0, _MAX_BACKOFF_CYCLES]).
    """
    AddonSettings.set_setting(
        EPG_BACKOFF_CYCLES_KEY,
        str(max(0, min(n, _MAX_BACKOFF_CYCLES))),
        store=LOCAL,
    )


def compute_signal_delay(backoff_cycles: int) -> int:
    """Return the IPTV-Manager signal delay in seconds for the given backoff level.

    :param int backoff_cycles: Number of consecutive "empty" cycles seen so far.
    :return: Delay in seconds (30 – 600).
    :rtype: int
    """
    return min(30 * (1 + backoff_cycles), 600)


def build_enrich_queue(
    all_programmes: List[Tuple[str, str, float, bool, bool]],
    cache: Dict[str, dict],
) -> List[_QueueEntry]:
    """Build an ordered enrichment queue from all collected programmes.

    Only uncached programmes are queued.  Ordering (strict):
      1. Currently-airing  (is_now=True),  in channel/programme order
      2. Next slot per channel (is_next=True, is_now=False), in order
      3. Future slots by start_ts ascending
      4. Past slots by start_ts descending (most-recent first)

    :param all_programmes: List of (contentItemId, assetId, start_ts, is_now, is_past).
    :param cache: Current detail cache (to skip already-enriched items).
    :return: Ordered queue of [contentItemId, assetId, start_ts, is_now_int].
    :rtype: list
    """
    uncached = [p for p in all_programmes if p[0] not in cache]
    n_cached = len(all_programmes) - len(uncached)

    now_entries = [[p[0], p[1], p[2], 1]
                   for p in uncached if p[3] and not p[4]]
    next_entries = [[p[0], p[1], p[2], 0]
                    for p in uncached if not p[3] and not p[4] and
                    p[2] > time.time()]
    past_entries = [[p[0], p[1], p[2], 0]
                    for p in uncached if p[4]]

    # Future: sort soonest first
    next_entries.sort(key=lambda e: e[2])
    # Past: sort most-recent first
    past_entries.sort(key=lambda e: e[2], reverse=True)

    result = now_entries + next_entries + past_entries
    Logger.debug(
        "NLZIET EPG: queue rebuilt: now=%d future=%d past=%d → total=%d"
        " (from %d programmes, %d already cached)",
        len(now_entries), len(next_entries), len(past_entries),
        len(result), len(all_programmes), n_cached,
    )
    return result


def fetch_and_cache(
    batch: List[_QueueEntry],
    http_headers: Dict[str, str],
) -> int:
    """Fetch item/detail for up to ENRICH_BATCH_SIZE items and update cache.

    :param batch: Queue entries to process (≤ ENRICH_BATCH_SIZE).
    :param http_headers: Auth + app headers for API requests.
    :return: Number of items newly fetched (0 = nothing new, no signal needed).
    :rtype: int
    """
    if not batch:
        return 0

    Logger.debug("NLZIET EPG: fetch_and_cache: batch=%d", len(batch))
    cache = load_detail_cache()
    newly_fetched = 0
    already_cached = 0

    for entry in batch[:EPG_ENRICH_BATCH_SIZE]:
        content_item_id = entry[0]
        asset_id = entry[1]

        if content_item_id in cache:
            already_cached += 1
            continue  # already cached from a parallel call

        Logger.debug("NLZIET EPG: fetching detail for %s/%s", content_item_id, asset_id)
        url = API_V9_EPG_ITEM_DETAIL.format(content_item_id, asset_id)
        raw = UriHandler.open(url, additional_headers=http_headers)
        if not raw:
            Logger.warning("NLZIET EPG: No detail data for %s", content_item_id)
            continue

        detail = JsonHelper(raw)
        content = detail.get_value("content", fallback={})

        description = content.get("description") or None
        genre: Optional[str] = None
        genres = content.get("genres") or []
        if isinstance(genres, list) and genres:
            genre = genres[0].get("name") or None

        cache[content_item_id] = {
            "description": description,
            "genre": genre,
            "fetched_at": time.time(),
        }
        newly_fetched += 1

    if newly_fetched:
        save_detail_cache(cache)
        Logger.debug(
            "NLZIET EPG: enriched %d items (skipped %d already cached, cache size: %d)",
            newly_fetched, already_cached, len(cache),
        )
    else:
        Logger.debug("NLZIET EPG: fetch_and_cache: nothing new (skipped %d already cached)",
                     already_cached)

    return newly_fetched
