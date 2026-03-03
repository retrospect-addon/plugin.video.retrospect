# SPDX-License-Identifier: GPL-3.0-or-later
"""NLZIET EPG description/genre enrichment helpers.

These are module-level (stateless) functions so they can be called from both
the channel (``chn_nlziet.py``) and the background service (``retroservice.py``)
without instantiating a full Channel object.

Queue format (stored in LocalSettings under ``EPG_ENRICH_QUEUE_KEY``):
    [[contentItemId, assetId, start_ts, is_now], ...]

Cache format (stored in LocalSettings under ``EPG_DETAIL_CACHE_KEY``):
    {contentItemId: {"description": str|None,
                     "genre":       str|None,
                     "fetched_at":  float}}
"""

import json
import time
from typing import Dict, List, Optional, Tuple

from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler

from api import (
    API_V9_EPG_ITEM_DETAIL,
    EPG_CACHE_TTL_DAYS,
    EPG_DETAIL_CACHE_KEY,
    EPG_ENRICH_BATCH_SIZE,
    EPG_ENRICH_QUEUE_KEY,
)

# Type alias for a queue entry
_QueueEntry = List  # [contentItemId, assetId, start_ts, is_now_int]


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


def load_enrich_queue() -> List[_QueueEntry]:
    """Load the enrichment queue from LocalSettings.

    :return: Ordered list of [contentItemId, assetId, start_ts, is_now_int].
    :rtype: list
    """
    raw = AddonSettings.get_setting(EPG_ENRICH_QUEUE_KEY, store=LOCAL) or ""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        Logger.warning("NLZIET EPG: Could not parse enrich queue, resetting")
        return []


def save_enrich_queue(queue: List[_QueueEntry]) -> None:
    """Save the enrichment queue to LocalSettings.

    :param list queue: Queue to persist.
    """
    AddonSettings.set_setting(EPG_ENRICH_QUEUE_KEY, json.dumps(queue), store=LOCAL)


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

    now_entries = [[p[0], p[1], p[2], 1]
                   for p in uncached if p[3] and not p[4]]
    next_entries = [[p[0], p[1], p[2], 0]
                    for p in uncached if not p[3] and not p[4] and
                    # "next" = closest future slot; we include everything future
                    # and let priority sorting handle it
                    p[2] > time.time()]
    past_entries = [[p[0], p[1], p[2], 0]
                    for p in uncached if p[4]]

    # Future: sort soonest first
    next_entries.sort(key=lambda e: e[2])
    # Past: sort most-recent first
    past_entries.sort(key=lambda e: e[2], reverse=True)

    return now_entries + next_entries + past_entries


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

    cache = load_detail_cache()
    newly_fetched = 0

    for entry in batch[:EPG_ENRICH_BATCH_SIZE]:
        content_item_id = entry[0]
        asset_id = entry[1]

        if content_item_id in cache:
            continue  # already cached from a parallel call

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
        Logger.debug("NLZIET EPG: Enriched %d items (cache size: %d)",
                     newly_fetched, len(cache))

    return newly_fetched
