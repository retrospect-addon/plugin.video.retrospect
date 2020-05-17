# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.authentication.gigyahandler import GigyaHandler
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestGigyaHandler(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestGigyaHandler, self).__init__(methodName)

        self.user_name = os.environ.get("MEDIALAAN_USERNAME")
        self.password = os.environ.get("MEDIALAAN_PASSWORD")
        self.api_key = "3_OEz9nzakKMkhPdUnz41EqSRfhJg5z9JXvS4wUORkqNf2M2c1wS81ilBgCewkot97"

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

    def test_init_handler(self):
        a = GigyaHandler("vtm.be", self.api_key)
        self.assertIsNotNone(a)

    def test_invalid_username(self):
        a = GigyaHandler("vtm.be", self.api_key)
        res = a.log_on("nobody", "secret")
        self.assertFalse(res.logged_on)

    @unittest.skipIf("MEDIALAAN_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated(self):
        a = GigyaHandler("vtm.be", self.api_key)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)

    @unittest.skipIf("MEDIALAAN_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated_after_login(self):
        a = GigyaHandler("vtm.be", self.api_key)
        auth_session = a.log_on(self.user_name, self.password)
        self.assertTrue(auth_session.logged_on)

        a = GigyaHandler("vtm.be", self.api_key)
        authenticated = a.active_authentication()
        self.assertEqual(self.user_name, authenticated.username)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__signature)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__signature_timestamp)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__user_id)

    @unittest.skipIf("MEDIALAAN_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on(self):
        a = GigyaHandler("vtm.be", self.api_key)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__signature)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__signature_timestamp)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._GigyaHandler__user_id)

    @unittest.skipIf("MEDIALAAN_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_off(self):
        a = GigyaHandler("vtm.be", self.api_key)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        a.log_off(self.user_name)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)
