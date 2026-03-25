# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import unittest.mock

from resources.lib.helpers.useragenthelper import FALLBACK_USER_AGENT, UserAgentHelper


class TestUserAgentHelper(unittest.TestCase):

    @unittest.mock.patch("resources.lib.helpers.useragenthelper.UserAgentHelper._load_cached_user_agents")
    def test_get_user_agent_prefers_cached_value(
            self, mock_load: unittest.mock.MagicMock) -> None:
        """get_user_agent() returns the freshest cached browser User-Agent."""

        mock_load.return_value = ["Browser/2.0", "Browser/1.0"]

        self.assertEqual("Browser/2.0", UserAgentHelper.get_user_agent())


    @unittest.mock.patch("resources.lib.helpers.useragenthelper.UserAgentHelper._fetch_and_cache_user_agents")
    @unittest.mock.patch("resources.lib.helpers.useragenthelper.UserAgentHelper._load_cached_user_agents")
    def test_get_user_agent_fetches_when_cache_missing(
            self,
            mock_load: unittest.mock.MagicMock,
            mock_fetch: unittest.mock.MagicMock) -> None:
        """get_user_agent() fetches from upstream when the cache is empty."""

        mock_load.return_value = None
        mock_fetch.return_value = ["Fetched/3.0"]

        self.assertEqual("Fetched/3.0", UserAgentHelper.get_user_agent())
        mock_fetch.assert_called_once()


    @unittest.mock.patch("resources.lib.helpers.useragenthelper.UserAgentHelper._fetch_and_cache_user_agents")
    @unittest.mock.patch("resources.lib.helpers.useragenthelper.UserAgentHelper._load_cached_user_agents")
    def test_get_user_agent_uses_fallback_when_fetch_fails(
            self,
            mock_load: unittest.mock.MagicMock,
            mock_fetch: unittest.mock.MagicMock) -> None:
        """get_user_agent() falls back to the bundled UA when cache and fetch both fail."""

        mock_load.return_value = None
        mock_fetch.return_value = None

        self.assertEqual(FALLBACK_USER_AGENT, UserAgentHelper.get_user_agent())
