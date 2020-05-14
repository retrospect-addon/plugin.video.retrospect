# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from tests.channel_tests.channeltest import ChannelTest


class TestNpoChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNpoChannel, self).__init__(methodName, "channel.nos.nos2010", "uzgjson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 8, "No items found in mainlist")

    def test_live_radio(self):
        self._test_folder_url("http://radio-app.omroep.nl/player/script/player.js", 8)

    def test_live_tv(self):
        self._test_folder_url("https://www.npostart.nl/live", 10)

    def test_categories(self):
        self._test_folder_url("https://www.npostart.nl/programmas", 5)

    def test_recent_week_list(self):
        self._test_folder_url("#recent", 7)

    def test_alpha_listing(self):
        self._test_folder_url("#alphalisting", 27)

    def test_alpha_sub_listing(self):
        self._test_folder_url(
            "https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&az=A&"
            "tileMapping=normal&tileType=teaser&pageType=catalogue",
            headers={"X-Requested-With": "XMLHttpRequest"},
            expected_results=50
        )

    def test_full_alpha_list(self):
        self._test_folder_url(
            "https://start-api.npo.nl/page/catalogue?pageSize=25",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=25, exact_results=True
        )

    def test_full_alpha_sub_list(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/BV_101396526/episodes?pageSize=5",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=5
        )
        # More pages should be preeent (requested 5, will be more there)
        folders = [item for item in items if item.type == "folder"]
        self.assertGreaterEqual(len(folders), 1)

    def test_tv_show_listing(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/NOSjnl2000/episodes?pageSize=10",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=11, exact_results=True
        )
        # More pages should be preeent (requested 5, will be more there)
        folders = [item for item in items if item.type == "folder"]
        self.assertGreaterEqual(len(folders), 1)

    def test_guide_day_list(self):
        import datetime
        day = datetime.datetime.now() - datetime.timedelta(days=1)
        self._test_folder_url(
            "https://start-api.npo.nl/epg/{:04d}-{:02d}-{:02d}?type=tv".format(day.year, day.month, day.day),
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=25
        )

    def test_search_extend(self):
        self._test_folder_url(
            "https://www.npostart.nl/search/extended?page=4&query=test&filter=episodes&"
            "dateFrom=2014-01-01&tileMapping=search&tileType=asset&pageType=search",
            expected_results=5,
            headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def test_update_stream_pow(self):
        url = "POW_04508304"
        self._test_video_url(url)
