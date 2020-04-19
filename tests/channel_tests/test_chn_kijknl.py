# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from tests.channel_tests.channeltest import ChannelTest


class TestKijkNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestKijkNlChannel, self).__init__(methodName, "chn_kijknl", None)

    def test_sbs6(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "sbs")
        self.assertIsNotNone(chn)

    def test_sbs9(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "sbs9")
        self.assertIsNotNone(chn)

    def test_veronica(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "veronica")
        self.assertIsNotNone(chn)

    def test_net5(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "net5")
        self.assertIsNotNone(chn)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)

    def test_main_list_none_kijk(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel(self._channel, "sbs")
        self.test_main_list()

    def test_last_week(self):
        self._test_folder_url("#lastweek", expected_results=7, exact_results=True)

    def test_week_day(self):
        self._test_folder_url("https://api.kijk.nl/v1/default/sections/missed-all-20191011",
                              expected_results=10)

    def test_main_list_html(self):
        with self.assertRaises(ValueError):
            self._test_folder_url("https://www.kijk.nl/programmas",
                                  expected_results=0, exact_results=True)

    def test_poplular(self):
        self._test_folder_url(
            "https://api.kijk.nl/v2/default/sections/popular_PopularVODs?offset=0",
            expected_results=50)

    def test_update_embedded_mpd_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/4kibjRMBhWJI?id=kijkapp&format=DASH&drm=CENC")

    def test_update_embedded_mpd_encrypted_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/P74c4ckPaE9?id=kijkapp&format=DASH&drm=CENC")

    def test_graphql_main_list(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bprograms%28programTypes%3A%5BSERIES%5D"
            "%2Climit%3A10%29%7Bitems%7B__typename%2Ctitle%2Cdescription%2Cguid%2Cupdated%2C"
            "seriesTvSeasons%7Bid%7D%2CimageMedia%7Burl%2Clabel%7D%7D%7D%7D",
            expected_results=10
        )

    def test_graphql_multi_season_show(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bprograms%28guid%3A%22C5IYffeeRR8%22%29"
            "%7Bitems%7BseriesTvSeasons%7Bid%2Ctitle%2CseasonNumber%2C__typename%7D%7D%7D%7D",
            expected_results=3
        )

    def test_graphql_season_list(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?operationName=programs&variables=%7B%22tvSeasonId%22"
            "%3A%20%22110507048401%22%2C%20%22skip%22%3A%200%2C%20%22programTypes%22%3A%20%22EPISODE"
            "%22%2C%20%22limit%22%3A%20100%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22"
            "version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2276458972ecff15df43ab75bd550d6a85ffd0e"
            "90fee2c267d14df087065ee37e2%22%7D%7D",
            expected_results=2
        )

    def test_graphql_mpd_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql")
        item.metaData["sources"] = [
            {
                "type": "dash",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/index.mpd",
                "drm": None,
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def test_graphql_m3u8_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql")
        item.metaData["sources"] = [
            {
                "type": "m3u8",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/master.m3u8",
                "drm": None,
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def test_graphql_drm_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql")
        item.metaData["sources"] = [
            {
                "type": "dash",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/index.mpd",
                "drm": {
                    "widevine": {
                        "releasePid": "dBujAGhE20a7",
                        "url": "https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm?releasePid=dBujAGhE20a7&form=json&schema=1.0",
                        "certificateUrl": None,
                        "processSpcUrl": None
                    }
                },
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())
