# SPDX-License-Identifier: GPL-3.0-or-later

import io
import os
import shutil
import unittest

from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.urihandler import UriHandler


class TestSubtitleHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler()

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(Config.cacheDir):
            shutil.rmtree(Config.cacheDir)

    def setUp(self):
        if os.path.isdir(Config.cacheDir):
            shutil.rmtree(Config.cacheDir)
        os.makedirs(Config.cacheDir)

    def tearDown(self):
        pass

    def test_webvtt_download(self):
        url = "https://cdn.rieter.net/testfiles/test_subtitle.vtt"
        srt = SubtitleHelper.download_subtitle(url, format='webvtt')
        self.assertIsNot("", srt)
        self.assertIsNotNone(srt)
        self.assertTrue(os.path.isfile(srt))

        # Check the content
        with io.open(srt, mode='r', encoding='utf-8') as fp:
            raw = fp.read()

        self.assertIsNot("", raw)

    def test_webvtt(self):
        with io.open(os.path.join("tests", "data", "webvtt001.vtt"), mode='r', encoding='utf-8') as fp:
            raw = fp.read()

        # noinspection PyUnresolvedReferences
        srt = SubtitleHelper._SubtitleHelper__convert_web_vtt_to_srt(raw)
        self.assertIsNot("", srt)
