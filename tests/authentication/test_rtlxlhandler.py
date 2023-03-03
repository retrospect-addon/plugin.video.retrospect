# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.authentication.rtlxlhandler import RtlXlHandler


class TestRtlXlHandler(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRtlXlHandler, self).__init__(methodName)

        self.user_name = os.environ.get("RTLXL_USERNAME")
        self.password = os.environ.get("RTLXL_PASSWORD")
        self.api_key = "3_R0XjstXd4MpkuqdK3kKxX20icLSE3FB27yQKl4zQVjVpqmgSyRCPKKLGdn5kjoKq"

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

    def test_init_handler(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)
        self.assertIsNotNone(a)

    def test_invalid_username(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)
        res = a.log_on("nobody", "secret")
        self.assertFalse(res.logged_on)

    @unittest.skipIf(not os.environ.get("RTLXL_USERNAME"), "Not testing login without credentials")
    def test_is_authenticated(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)

    @unittest.skipIf(not os.environ.get("RTLXL_USERNAME"), "Not testing login without credentials")
    def test_is_authenticated_after_login(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)
        auth_session = a.log_on(self.user_name, self.password)
        self.assertTrue(auth_session.logged_on)

        a = RtlXlHandler("rtlxl.nl", self.api_key)
        authenticated = a.active_authentication()
        self.assertEqual(self.user_name, authenticated.username)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__signature)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__signature_timestamp)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__user_id)

    @unittest.skipIf(not os.environ.get("RTLXL_USERNAME"), "Not testing login without credentials")
    def test_log_on(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)

        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)

        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__signature)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__signature_timestamp)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(a._RtlXlHandler__user_id)

    @unittest.skipIf(not os.environ.get("RTLXL_USERNAME"), "Not testing login without credentials")
    def test_log_off(self):
        a = RtlXlHandler("rtlxl.nl", self.api_key)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        a.log_off(self.user_name)
        res = a.active_authentication()
        self.assertFalse(res.logged_on)
        self.assertIsNone(res.username)
