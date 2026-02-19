# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from resources.lib.urihandler import UriHandler

from .channeltest import ChannelTest


class TestNLZietChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNLZietChannel, self).__init__(methodName, "channel.nlziet.nlziet", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_process_folder_list_login_failure(self):
        """process_folder_list returns None when login fails."""
        original_log_on = self.channel.log_on
        try:
            self.channel.log_on = lambda *a, **kw: False
            result = self.channel.process_folder_list(None)
            self.assertIsNone(result)
        finally:
            self.channel.log_on = original_log_on


class TestNLZietChannelLive(TestNLZietChannel):
    """Live integration tests — requires NLZIET_USERNAME and NLZIET_PASSWORD."""

    @classmethod
    def setUpClass(cls):
        cls.username = os.getenv("NLZIET_USERNAME")
        cls.password = os.getenv("NLZIET_PASSWORD")
        if not cls.username or not cls.password:
            raise unittest.SkipTest("NLZIET credentials not in environment.")
        super().setUpClass()

        # Clear any cached mock tokens left by TestNLZIETAuthMocked, then do a
        # one-time real authentication and pre-store the first available profile
        # (profile 0) so that each setUp() uses the cached-token path and never
        # triggers the interactive profile-selection dialog.
        from resources.lib.addonsettings import AddonSettings, LOCAL
        from resources.lib.authentication.nlzietoauth2handler import NLZIETOAuth2Handler
        from resources.lib.authentication.authenticator import Authenticator
        for client_id in (NLZIETOAuth2Handler.WEB_CLIENT_ID, NLZIETOAuth2Handler.TV_CLIENT_ID):
            prefix = "nlziet_oauth2_{}_".format(client_id)
            AddonSettings.set_setting("{}access_token".format(prefix), "", store=LOCAL)
            AddonSettings.set_setting("{}refresh_token".format(prefix), "", store=LOCAL)
            AddonSettings.set_setting("{}expires_at".format(prefix), "", store=LOCAL)
        AddonSettings.set_setting(NLZIETOAuth2Handler.AUTH_METHOD_SETTING, "web", store=LOCAL)
        handler = NLZIETOAuth2Handler(use_device_flow=False)
        auth = Authenticator(handler)
        result = auth.log_on(username=cls.username, password=cls.password)
        if not result.logged_on:
            raise unittest.SkipTest("NLZIET live login failed in setUpClass.")
        profiles = handler.list_profiles()
        if profiles:
            handler.set_profile(profiles[0]["id"])

    def setUp(self):
        super().setUp()
        if not self.channel.log_on(self.username, self.password):
            self.skipTest("NLZIET login failed.")

    def test_login_succeeds(self):
        """Live: log_on() with real credentials succeeds."""
        self.assertTrue(self.channel.loggedOn)


class TestNLZietChannelMocked(TestNLZietChannelLive):
    """Mocked channel tests — always runs, uses NLZietMockDispatcher."""

    _mock_dispatcher = None
    _original_open = None

    @classmethod
    def setUpClass(cls):
        # Skip TestNLZietChannelLive.setUpClass (credential guard); go straight to ChannelTest.
        super(TestNLZietChannelLive, cls).setUpClass()

        from tests.authentication.nlziet_mocks import NLZietMockDispatcher
        cls.username = "test@example.com"
        cls.password = "mock_password"
        cls._mock_dispatcher = NLZietMockDispatcher()
        cls._original_open = UriHandler.instance().open
        uri_instance = UriHandler.instance()
        dispatcher = cls._mock_dispatcher

        def mock_open(uri, proxy=None, params=None, data=None, json=None,
                      referer=None, additional_headers=None, no_cache=False,
                      force_text=False, force_cache_duration=None, method=""):
            return dispatcher.dispatch(
                uri, uri_instance,
                params=params, data=data, json=json, method=method,
                additional_headers=additional_headers,
            )

        uri_instance.open = mock_open

    @classmethod
    def tearDownClass(cls):
        if cls._original_open is not None:
            UriHandler.instance().open = cls._original_open
        super().tearDownClass()

    def setUp(self):
        if self._mock_dispatcher:
            self._mock_dispatcher.reset()
        UriHandler.delete_cookie(domain=".nlziet.nl")
        # Create channel and log in via mock (skips TestNLZietChannelLive.setUp credential guard).
        super(TestNLZietChannelLive, self).setUp()
        # Pre-set the profile so log_on skips the interactive selection dialog.
        from tests.authentication.nlziet_mocks import MOCK_PROFILE_LIST
        from resources.lib.addonsettings import AddonSettings, LOCAL
        handler = self.channel._Channel__handler  # noqa: SLF001
        AddonSettings.set_setting(
            "{}profile_id".format(handler.prefix), MOCK_PROFILE_LIST[0]["id"], store=LOCAL)
        if not self.channel.log_on(self.username, self.password):
            self.fail("Mocked NLZIET login failed.")
