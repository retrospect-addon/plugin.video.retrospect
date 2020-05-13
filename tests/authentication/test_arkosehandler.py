# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import binascii
import os
import unittest

from resources.lib.authentication.arkosehandler import ArkoseHandler
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestArkoseHandler(unittest.TestCase):
    DeviceId = None

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestArkoseHandler, self).__init__(methodName)

        self.user_name = os.environ.get("DPLAY_USERNAME")
        self.password = os.environ.get("DPLAY_PASSWORD")

    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)
        TestArkoseHandler.DeviceId = binascii.hexlify(os.urandom(16)).decode()  # Should be .lower()

    @classmethod
    def tearDownClass(cls):
        Logger.instance().close_log()

    def tearDown(self):
        pass

    def setUp(self):
        if UriHandler.get_cookie("st", "disco-api.dplay.se"):
            UriHandler.delete_cookie(domain="disco-api.dplay.se")

    def test_init_handler(self):
        a = ArkoseHandler("dplay.se", TestArkoseHandler.DeviceId)
        self.assertIsNotNone(a)

    def test_lower_case_device_id_no_dash_after_init(self):
        # create faulty device ID
        device_id = TestArkoseHandler.DeviceId.upper()
        device_id_dash = "{}-{}".format(device_id[0:2], device_id[2:])
        a = ArkoseHandler("dplay.se", device_id_dash)
        self.assertEqual(TestArkoseHandler.DeviceId.lower(), a._device_id)

    def test_invalid_username(self):
        a = ArkoseHandler("dplay.se", TestArkoseHandler.DeviceId)
        logged_on = a.log_on("nobody", "secret")
        self.assertFalse(logged_on)

    @unittest.skipIf("DPLAY_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated(self):
        a = ArkoseHandler("dplay.se", TestArkoseHandler.DeviceId)
        authenticated = a.is_authenticated(self.user_name)
        self.assertFalse(authenticated)

    @unittest.skipIf("DPLAY_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_is_authenticated_after_login(self):
        a = ArkoseHandler("dplay.se", TestArkoseHandler.DeviceId)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)
        authenticated = a.is_authenticated(self.user_name)
        self.assertTrue(authenticated)

    @unittest.skipIf("DPLAY_USERNAME" not in os.environ, "Not testing login without credentials")
    def test_log_on(self):
        a = ArkoseHandler("dplay.se", TestArkoseHandler.DeviceId)
        logged_on = a.log_on(self.user_name, self.password)
        self.assertTrue(logged_on)

