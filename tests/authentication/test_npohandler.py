# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.authentication.npohandler import NpoHandler
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestNpoHandler(unittest.TestCase):
    DeviceId = None

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNpoHandler, self).__init__(methodName)

        self.user_name = os.environ.get("NPO_USERNAME")
        self.password = os.environ.get("NPO_PASSWORD")

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
        UriHandler.delete_cookie(domain="www.npostart.nl")
        UriHandler.delete_cookie(domain=".npostart.nl")

    def test_init_handler(self):
        a = NpoHandler("npo.nl")
        self.assertIsNotNone(a)

    def test_invalid_username(self):
        a = NpoHandler("npo.nl")
        res = a.log_on("nobody", "secret")
        self.assertFalse(res.logged_on)

    @unittest.skipIf("NPO_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated(self):
        a = NpoHandler("npo.nl")
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)

    @unittest.skipIf("NPO_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated_after_login(self):
        a = NpoHandler("npo.nl")
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        authenticated = a.active_authentication()
        self.assertEqual(self.user_name, authenticated.username)

    @unittest.skipIf("NPO_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on(self):
        a = NpoHandler("npo.nl")
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)

    @unittest.skipIf("NPO_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_off(self):
        a = NpoHandler("npo.nl")
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        a.log_off(self.user_name)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)
