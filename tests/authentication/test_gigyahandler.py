# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest
import uuid

from resources.lib.authentication.gigyahandler import GigyaHandler
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestGigyaHandler(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestGigyaHandler, self).__init__(methodName)

        self.user_name = os.environ.get("VIDEOLAND_USERNAME")
        self.password = os.environ.get("VIDEOLAND_PASSWORD")
        self.api_key_3 = "3_t2Z1dFrbWR-IjcC-Bod1kei6W91UKmeiu3dETVG5iKaY4ILBRzVsmgRHWWo0fqqd"
        self.api_key_4 = "4_hRanGnYDFjdiZQfh-ghhhg"
        self.realm = "videoland.com"
        self.__device_id = str(uuid.uuid1())

    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)

    @classmethod
    def tearDownClass(cls):
        Logger.instance().close_log()

    def tearDown(self):
        pass

    def setUp(self):
        UriHandler.delete_cookie(domain=".gigya.com")
        UriHandler.delete_cookie(domain=f".{self.realm}")

    def test_init_handler(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        self.assertIsNotNone(a)

    @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"), "Not testing login without credentials")
    def test_log_on(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)

        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)

    @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"), "Not testing login without credentials")
    def test_is_authenticated_without_login(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)

    @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"), "Not testing login without credentials")
    def test_is_authenticated_after_login(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        auth_session = a.log_on(self.user_name, self.password)
        self.assertTrue(auth_session.logged_on)

        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        authenticated = a.active_authentication()
        self.assertEqual(self.user_name, authenticated.username)

    def test_invalid_username(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        res = a.log_on("nobody", "secret")
        self.assertFalse(res.logged_on)

    @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"), "Not testing login without credentials")
    def test_log_off(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        a.log_off(self.user_name)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)

    @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"), "Not testing login without credentials")
    def test_token_fetch(self):
        a = GigyaHandler(self.realm, self.api_key_3, self.api_key_4, self.__device_id)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        token = a.get_authentication_token()
        self.assertIsNotNone(token)
