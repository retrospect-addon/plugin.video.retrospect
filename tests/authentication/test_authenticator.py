# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import binascii
import os
import unittest

from resources.lib.authentication.rtlxlhandler import RtlXlHandler
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestAuthenticator(unittest.TestCase):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestAuthenticator, self).__init__(methodName)

        self.user_name = os.environ.get("RTLXL_USERNAME")
        self.password = os.environ.get("RTLXL_PASSWORD")
        self.device_id = binascii.hexlify(os.urandom(16)).decode()
        self.rtl_api_key = "3_R0XjstXd4MpkuqdK3kKxX20icLSE3FB27yQKl4zQVjVpqmgSyRCPKKLGdn5kjoKq"

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
        UriHandler.delete_cookie(domain=".sso.rtl.nl")

    def test_init_authenticator_no_handler(self):
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            Authenticator(None)

    def test_init_authenticator_incorrect_type(self):
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            Authenticator("handler")

    def test_init_authenticator(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        self.assertIsNotNone(a)

    def test_login_no_username(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on("", "secret")
        self.assertFalse(res.logged_on)

    def test_login_no_password(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on("username", "")
        self.assertFalse(res.logged_on)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_current_user(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        a.log_on(self.user_name, self.password)
        h_user = h.active_authentication()
        a_user = a.active_authentication()
        self.assertEqual(h_user.username, a_user.username)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on(self.user_name, self.password)
        self.assertTrue(res.logged_on)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on_twice(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on(self.user_name, self.password)
        self.assertTrue(res.logged_on)
        res = a.log_on(self.user_name, self.password)
        self.assertTrue(res.logged_on)
        self.assertTrue(res.existing_login)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_off(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on(self.user_name, self.password)
        self.assertTrue(res.logged_on)
        a.log_off(self.user_name)
        self.assertFalse(a.active_authentication().logged_on)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on_without_log_off(self):
        h = RtlXlHandler("rtlxl.nl", self.rtl_api_key)
        a = Authenticator(h)
        res = a.log_on(self.user_name, self.password)
        self.assertTrue(res.logged_on)
        user_name = self.user_name.replace("lf@m", "lf2@m")
        res = a.log_on(user_name, self.password)
        self.assertTrue(res.logged_on)
        self.assertEqual(user_name, a.active_authentication().username)
