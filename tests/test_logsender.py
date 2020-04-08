from future.utils import PY2

import unittest
import sys
import os

if PY2:
    # noinspection PyCompatibility,PyUnresolvedReferences
    reload(sys)
    # noinspection PyUnresolvedReferences
    sys.setdefaultencoding("utf-8")  # @UndefinedVariable

from resources.lib.helpers.logsender import LogSender
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger


class TestLogSender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        self.__api_key = "random_fake_api_key"
        self.__pastebin_key = "not_used"
        self.__hastebin_key = "not_required"
        self.__logger = Logger.instance()
        self.__logFile = os.path.join(os.path.dirname(__file__), "data", "smalllog.log")
        self.__logFile = os.path.abspath(self.__logFile)
        self.__proxy = None  # ProxyInfo("localhost", 8888)
        self.__userKey = ''  # the userKey is reset whenever Login call is successful
        UriHandler.create_uri_handler(ignore_ssl_errors=False)

    def test_LogSender_init_no_api(self):
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            LogSender(None)

    def test_LogSender_init(self):
        log_sender = LogSender(self.__api_key, logger=self.__logger, proxy=self.__proxy)
        # noinspection PyUnresolvedReferences
        self.assertEqual(self.__api_key, log_sender._LogSender__apiKey)

    def test_LogSender_Send_NoName(self):
        log_sender = LogSender(self.__api_key, logger=self.__logger, proxy=self.__proxy)
        with self.assertRaises(ValueError):
            log_sender.send("", "")

    def test_LogSender_Send_NoPath(self):
        log_sender = LogSender(self.__api_key, logger=self.__logger, proxy=self.__proxy)
        with self.assertRaises(ValueError):
            log_sender.send("name", "")

    @unittest.skip("Pastebin no longer used.")
    def test_LogSender_SendPlainText(self):
        log_sender = LogSender(self.__pastebin_key, logger=self.__logger, proxy=self.__proxy, mode="pastebin")
        url = log_sender.send("name", "RAW data", user_key=self.__userKey)
        self.assertIsNotNone(url)
        self.assertTrue("https://pastebin.com" in url)

    def test_LogSender_HasteSendPlainText(self):
        log_sender = LogSender(self.__hastebin_key, logger=self.__logger, proxy=self.__proxy, mode="hastebin")
        url = log_sender.send("name", "RAW data", user_key=self.__userKey)
        self.assertIsNotNone(url)
        self.assertTrue("https://paste.kodi.tv" in url)

    def test_LogSender_SendFile_HasteBin(self):
        log_sender = LogSender(self.__hastebin_key, logger=self.__logger, proxy=self.__proxy, mode="hastebin")
        log_file = os.path.join(os.path.dirname(__file__), "data", "largelogfile.log")
        url = log_sender.send_file("name", log_file)
        self.assertIsNotNone(url)
        self.assertTrue("https://paste.kodi.tv" in url)

    def test_LogSender_SendLargeFile_HasteBin(self):
        log_sender = LogSender(self.__hastebin_key, logger=self.__logger, proxy=self.__proxy, mode="hastebin")
        url = log_sender.send_file("name", self.__logFile)
        self.assertIsNotNone(url)
        self.assertTrue("https://paste.kodi.tv" in url)

    @unittest.skip("Pastebin no longer used.")
    def test_LogSender_SendFile_PasteBin(self):
        log_sender = LogSender(self.__pastebin_key, logger=self.__logger, proxy=self.__proxy, mode="pastebin")
        url = log_sender.send_file("name", self.__logFile, user_key=self.__userKey)
        self.assertIsNotNone(url)
        self.assertTrue("pastebin.com" in url)

