# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.settings.localsettings import LocalSettings


class _FakeChannel:
    """Minimal stand-in for a Channel with an ``id`` attribute."""

    def __init__(self, channel_id):
        self.id = channel_id


class TestSearchHistory(unittest.TestCase):
    """Verify that profile-scoped search keys produce isolated histories."""

    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        local_settings_file = os.path.join(Config.profileDir, "settings.json")
        if os.path.isfile(local_settings_file):
            os.remove(local_settings_file)

    def _store(self):
        return LocalSettings(Config.profileDir, Logger.instance())

    # -- key construction ---------------------------------------------------

    def test_no_profile_uses_plain_key(self):
        """Without a profile, the key is just ``search``."""
        channel = _FakeChannel("channel.nlziet.nlziet")
        store = self._store()

        store.set_setting("search", ["cats"], channel)
        self.assertEqual(store.get_setting("search", channel, []), ["cats"])

    def test_profile_scoped_key(self):
        """With a profile, the key is ``search:<profile_id>``."""
        channel = _FakeChannel("channel.nlziet.nlziet")
        store = self._store()

        key = "search:profile-abc"
        store.set_setting(key, ["dogs"], channel)
        self.assertEqual(store.get_setting(key, channel, []), ["dogs"])

    def test_profiles_are_isolated(self):
        """Different profile keys must not share history."""
        channel = _FakeChannel("channel.nlziet.nlziet")
        store = self._store()

        store.set_setting("search:profile-adult", ["thriller"], channel)
        store.set_setting("search:profile-kids", ["cartoon"], channel)

        self.assertEqual(
            store.get_setting("search:profile-adult", channel, []),
            ["thriller"],
        )
        self.assertEqual(
            store.get_setting("search:profile-kids", channel, []),
            ["cartoon"],
        )

    def test_profile_key_does_not_affect_plain_key(self):
        """Profile-scoped history and plain history are independent."""
        channel = _FakeChannel("channel.nlziet.nlziet")
        store = self._store()

        store.set_setting("search", ["global"], channel)
        store.set_setting("search:profile-123", ["scoped"], channel)

        self.assertEqual(store.get_setting("search", channel, []), ["global"])
        self.assertEqual(
            store.get_setting("search:profile-123", channel, []), ["scoped"]
        )


if __name__ == "__main__":
    unittest.main()
