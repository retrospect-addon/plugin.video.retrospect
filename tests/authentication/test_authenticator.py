# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class TestAuthenticator(unittest.TestCase):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestAuthenticator, self).__init__(methodName)

        self.user_name = os.environ.get("DPLAY_USERNAME")

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
        pass
