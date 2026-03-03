# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for the NLZIET EPG enrichment helpers (epg_enrichment.py)."""

import json
import sys
import time
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, "channels/channel.nlziet/nlziet")

import epg_enrichment
from api import EPG_CACHE_TTL_DAYS, EPG_ENRICH_BATCH_SIZE


class TestDetailCacheIO(unittest.TestCase):
    """load_detail_cache / save_detail_cache round-trip and pruning."""

    def _make_entry(self, age_days=0):
        return {"description": "Test", "genre": "Nieuws", "fetched_at": time.time() - age_days * 86400}

    @patch("epg_enrichment.AddonSettings")
    def test_load_returns_empty_dict_when_no_setting(self, mock_settings):
        mock_settings.get_setting.return_value = ""
        result = epg_enrichment.load_detail_cache()
        self.assertEqual(result, {})

    @patch("epg_enrichment.AddonSettings")
    def test_load_returns_empty_dict_on_invalid_json(self, mock_settings):
        mock_settings.get_setting.return_value = "not-json"
        result = epg_enrichment.load_detail_cache()
        self.assertEqual(result, {})

    @patch("epg_enrichment.AddonSettings")
    def test_load_round_trips(self, mock_settings):
        cache = {"abc": self._make_entry(0)}
        mock_settings.get_setting.return_value = json.dumps(cache)
        result = epg_enrichment.load_detail_cache()
        self.assertIn("abc", result)

    @patch("epg_enrichment.AddonSettings")
    def test_save_prunes_stale_entries(self, mock_settings):
        fresh = self._make_entry(age_days=1)
        stale = self._make_entry(age_days=EPG_CACHE_TTL_DAYS + 1)
        cache = {"fresh_id": fresh, "stale_id": stale}

        epg_enrichment.save_detail_cache(cache)

        saved_json = mock_settings.set_setting.call_args[0][1]
        saved = json.loads(saved_json)
        self.assertIn("fresh_id", saved)
        self.assertNotIn("stale_id", saved)

    @patch("epg_enrichment.AddonSettings")
    def test_save_keeps_entries_within_ttl(self, mock_settings):
        cache = {"id1": self._make_entry(0), "id2": self._make_entry(1)}
        epg_enrichment.save_detail_cache(cache)
        saved = json.loads(mock_settings.set_setting.call_args[0][1])
        self.assertEqual(set(saved.keys()), {"id1", "id2"})


class TestQueueIO(unittest.TestCase):
    """load_enrich_queue / save_enrich_queue round-trip."""

    @patch("epg_enrichment.AddonSettings")
    def test_load_empty_queue(self, mock_settings):
        mock_settings.get_setting.return_value = ""
        self.assertEqual(epg_enrichment.load_enrich_queue(), [])

    @patch("epg_enrichment.AddonSettings")
    def test_save_and_load_queue(self, mock_settings):
        queue = [["id1", "asset1", 1000.0, 1], ["id2", "asset2", 2000.0, 0]]
        captured = []
        mock_settings.set_setting.side_effect = lambda *a, **kw: captured.append(a[1])
        epg_enrichment.save_enrich_queue(queue)

        mock_settings.get_setting.return_value = captured[0]
        result = epg_enrichment.load_enrich_queue()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "id1")


class TestBuildEnrichQueue(unittest.TestCase):
    """build_enrich_queue ordering and caching logic."""

    def _prog(self, cid, aid, start_ts, is_now=False, is_past=False):
        return (cid, aid, start_ts, is_now, is_past)

    def test_cached_items_excluded(self):
        now_ts = time.time()
        progs = [self._prog("cached", "a1", now_ts, is_now=True)]
        cache = {"cached": {"description": "x", "genre": "y", "fetched_at": now_ts}}
        queue = epg_enrichment.build_enrich_queue(progs, cache)
        self.assertEqual(queue, [])

    def test_now_items_come_first(self):
        now_ts = time.time()
        future_ts = now_ts + 3600
        past_ts = now_ts - 7200
        progs = [
            self._prog("future", "a1", future_ts, is_now=False, is_past=False),
            self._prog("now", "a2", now_ts, is_now=True, is_past=False),
            self._prog("past", "a3", past_ts, is_now=False, is_past=True),
        ]
        queue = epg_enrichment.build_enrich_queue(progs, {})
        ids = [e[0] for e in queue]
        self.assertEqual(ids[0], "now", "Currently-airing item must be first")

    def test_future_before_past(self):
        now_ts = time.time()
        progs = [
            self._prog("past", "a1", now_ts - 3600, is_past=True),
            self._prog("future", "a2", now_ts + 1800, is_past=False),
        ]
        queue = epg_enrichment.build_enrich_queue(progs, {})
        ids = [e[0] for e in queue]
        self.assertEqual(ids[0], "future")
        self.assertEqual(ids[1], "past")

    def test_future_sorted_soonest_first(self):
        now_ts = time.time()
        progs = [
            self._prog("far", "a1", now_ts + 7200, is_past=False),
            self._prog("soon", "a2", now_ts + 900, is_past=False),
        ]
        queue = epg_enrichment.build_enrich_queue(progs, {})
        self.assertEqual(queue[0][0], "soon")

    def test_past_sorted_most_recent_first(self):
        now_ts = time.time()
        progs = [
            self._prog("older", "a1", now_ts - 7200, is_past=True),
            self._prog("recent", "a2", now_ts - 1800, is_past=True),
        ]
        queue = epg_enrichment.build_enrich_queue(progs, {})
        self.assertEqual(queue[0][0], "recent")


class TestFetchAndCache(unittest.TestCase):
    """fetch_and_cache: API calls, batch limit, cache update."""

    def _make_detail_response(self, description="Omschrijving", genre="Nieuws"):
        return json.dumps({
            "content": {
                "description": description,
                "genres": [{"name": genre, "id": "News", "isObsolete": False}],
            }
        })

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_cache_hit_skips_api(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = json.dumps({
            "already_cached": {"description": "x", "genre": "y", "fetched_at": time.time()}
        })
        batch = [["already_cached", "asset1"]]

        result = epg_enrichment.fetch_and_cache(batch, {})

        self.assertEqual(result, 0)
        mock_uri.open.assert_not_called()

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_cache_miss_calls_api(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = ""
        mock_uri.open.return_value = self._make_detail_response()

        batch = [["new_id", "asset1"]]
        result = epg_enrichment.fetch_and_cache(batch, {"Authorization": "Bearer token"})

        self.assertEqual(result, 1)
        mock_uri.open.assert_called_once()

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_batch_limit_respected(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = ""
        mock_uri.open.return_value = self._make_detail_response()

        # Create more items than ENRICH_BATCH_SIZE
        batch = [["id{}".format(i), "asset{}".format(i)]
                 for i in range(EPG_ENRICH_BATCH_SIZE + 5)]
        result = epg_enrichment.fetch_and_cache(batch, {})

        self.assertLessEqual(mock_uri.open.call_count, EPG_ENRICH_BATCH_SIZE)

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_description_and_genre_stored_in_cache(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = ""
        mock_uri.open.return_value = self._make_detail_response(
            description="Met het laatste nieuws.", genre="Nieuws/actualiteiten")

        saved_data = {}

        def capture_set(key, value, store=None):
            saved_data[key] = value

        mock_settings.set_setting.side_effect = capture_set

        epg_enrichment.fetch_and_cache([["id1", "asset1"]], {})

        from api import EPG_DETAIL_CACHE_KEY
        self.assertIn(EPG_DETAIL_CACHE_KEY, saved_data)
        cache = json.loads(saved_data[EPG_DETAIL_CACHE_KEY])
        self.assertEqual(cache["id1"]["description"], "Met het laatste nieuws.")
        self.assertEqual(cache["id1"]["genre"], "Nieuws/actualiteiten")

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_missing_api_response_skipped(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = ""
        mock_uri.open.return_value = None  # simulates network failure

        result = epg_enrichment.fetch_and_cache([["id1", "asset1"]], {})
        self.assertEqual(result, 0)

    @patch("epg_enrichment.UriHandler")
    @patch("epg_enrichment.AddonSettings")
    def test_empty_batch_returns_zero(self, mock_settings, mock_uri):
        mock_settings.get_setting.return_value = ""
        result = epg_enrichment.fetch_and_cache([], {})
        self.assertEqual(result, 0)
        mock_uri.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class TestProlocCache(unittest.TestCase):
    """load_progloc_cache / save_progloc_cache round-trip and staleness."""

    @patch("epg_enrichment.AddonSettings")
    def test_load_empty_is_stale(self, mock_settings):
        mock_settings.get_setting.return_value = ""
        cache, is_stale = epg_enrichment.load_progloc_cache()
        self.assertEqual(cache, {})
        self.assertTrue(is_stale)

    @patch("epg_enrichment.AddonSettings")
    def test_load_fresh_not_stale(self, mock_settings):
        data = {"fetched_at": time.time(), "2026-01-01": []}
        mock_settings.get_setting.return_value = json.dumps(data)
        cache, is_stale = epg_enrichment.load_progloc_cache()
        self.assertFalse(is_stale)
        self.assertIn("2026-01-01", cache)

    @patch("epg_enrichment.AddonSettings")
    def test_load_expired_is_stale(self, mock_settings):
        data = {"fetched_at": time.time() - 400, "2026-01-01": []}  # > 300s TTL
        mock_settings.get_setting.return_value = json.dumps(data)
        _, is_stale = epg_enrichment.load_progloc_cache()
        self.assertTrue(is_stale)

    @patch("epg_enrichment.AddonSettings")
    def test_load_invalid_json_is_stale(self, mock_settings):
        mock_settings.get_setting.return_value = "not-json"
        cache, is_stale = epg_enrichment.load_progloc_cache()
        self.assertEqual(cache, {})
        self.assertTrue(is_stale)

    @patch("epg_enrichment.AddonSettings")
    def test_save_round_trips(self, mock_settings):
        saved = {}
        mock_settings.set_setting.side_effect = lambda k, v, store: saved.update({k: v})
        data = {"fetched_at": time.time(), "2026-01-01": [["cid1", "aid1", 1000.0, 2000.0]]}
        epg_enrichment.save_progloc_cache(data)
        from api import EPG_PROGLOC_CACHE_KEY
        self.assertIn(EPG_PROGLOC_CACHE_KEY, saved)
        loaded = json.loads(saved[EPG_PROGLOC_CACHE_KEY])
        self.assertIn("2026-01-01", loaded)


class TestBackoff(unittest.TestCase):
    """load_backoff_cycles / save_backoff_cycles / compute_signal_delay."""

    @patch("epg_enrichment.AddonSettings")
    def test_load_default_zero(self, mock_settings):
        mock_settings.get_setting.return_value = ""
        self.assertEqual(epg_enrichment.load_backoff_cycles(), 0)

    @patch("epg_enrichment.AddonSettings")
    def test_save_and_load(self, mock_settings):
        saved = {}
        mock_settings.set_setting.side_effect = lambda k, v, store: saved.update({k: v})
        epg_enrichment.save_backoff_cycles(5)
        from api import EPG_BACKOFF_CYCLES_KEY
        self.assertEqual(saved[EPG_BACKOFF_CYCLES_KEY], "5")

    @patch("epg_enrichment.AddonSettings")
    def test_save_clamps_max(self, mock_settings):
        saved = {}
        mock_settings.set_setting.side_effect = lambda k, v, store: saved.update({k: v})
        epg_enrichment.save_backoff_cycles(999)
        from api import EPG_BACKOFF_CYCLES_KEY
        self.assertEqual(int(saved[EPG_BACKOFF_CYCLES_KEY]),
                         epg_enrichment._MAX_BACKOFF_CYCLES)

    def test_compute_signal_delay_zero_cycles(self):
        self.assertEqual(epg_enrichment.compute_signal_delay(0), 30)

    def test_compute_signal_delay_grows(self):
        delay_1 = epg_enrichment.compute_signal_delay(1)
        delay_0 = epg_enrichment.compute_signal_delay(0)
        self.assertGreater(delay_1, delay_0)

    def test_compute_signal_delay_capped_at_600(self):
        self.assertEqual(epg_enrichment.compute_signal_delay(999), 600)
