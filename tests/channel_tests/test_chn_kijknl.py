# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from . channeltest import ChannelTest


class TestKijkNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestKijkNlChannel, self).__init__(methodName, "channel.sbsnl.kijknl", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)

    def test_last_week(self):
        self._test_folder_url("#lastweek", expected_results=7, exact_results=True)

    def test_update_embedded_mpd_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/vhlbVj34UM9?id=kijkapp&format=DASH&drm=CENC")

    def test_update_embedded_mpd_encrypted_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/P74c4ckPaE9?id=kijkapp&format=DASH&drm=CENC")

    def test_graphql_main_list(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bprograms%28programTypes%3A%5BSERIES%5D"
            "%2Climit%3A10%29%7Bitems%7B__typename%2Ctitle%2Cdescription%2Cguid%2Cupdated%2C"
            "seriesTvSeasons%7Bid%7D%2CimageMedia%7Burl%2Clabel%7D%7D%7D%7D",
            expected_results=8
        )

    def test_graphql_multi_season_show(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bprograms%28guid%3A%22C5IYffeeRR8%22%29"
            "%7Bitems%7BseriesTvSeasons%7Bid%2Ctitle%2CseasonNumber%2C__typename%7D%7D%7D%7D",
            expected_results=3
        )

    def test_graphql_season_list(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bprograms%28tvSeasonId%3A%22113154600206"
            "%22%2CprogramTypes%3AEPISODE%2Cskip%3A0%2Climit%3A100%29%7Bitems%7B__typename%2Ctitle"
            "%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia%7Burl%2Clabel"
            "%7D%2Ctype%2Csources%7Btype%2Cdrm%2Cfile%7D%2Cseries%7Btitle%7D%2CseasonNumber"
            "%2CtvSeasonEpisodeNumber%2ClastPubDate%7D%7D%7D",
            expected_results=2
        )

    def test_graphql_recent(self):
        self._test_folder_url("#recentgraphql", expected_results=7, exact_results=True)

    def test_graphql_mpd_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql-video")
        item.metaData["sources"] = [
            {
                "type": "dash",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-"
                        "7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/index.mpd",
                "drm": None,
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def test_graphql_m3u8_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql-video")
        item.metaData["sources"] = [
            {
                "type": "m3u8",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-"
                        "7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/master.m3u8",
                "drm": None,
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def test_graphql_drm_video(self):
        item = self._get_media_item("https://graph.kijk.nl/graphql-video")
        item.metaData["sources"] = [
            {
                "type": "dash",
                "file": "https://vod-kijk2-prod.talpatvcdn.nl/WWVxSdzb98j/068c2eb6-a8b0-615d-c9ce-"
                        "7bd80d25fcf4/WWVxSdzb98j_1586234515465.ism/index.mpd",
                "drm": {
                    "widevine": {
                        "releasePid": "dBujAGhE20a7",
                        "url": "https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm?"
                               "releasePid=dBujAGhE20a7&form=json&schema=1.0",
                        "certificateUrl": None,
                        "processSpcUrl": None
                    }
                },
                "__typename": "Source"
            }
        ]
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def test_graphql_search(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bsearch%28searchParam%3A%22wegmi%22"
            "%2CprogramTypes%3A%5BSERIES%2CEPISODE%5D%2Climit%3A50%29%7Bitems%7B__typename"
            "%2Ctitle%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia"
            "%7Burl%2Clabel%7D%2Ctype%2Csources%7Btype%2Cfile%2Cdrm%7D%2CseasonNumber"
            "%2CtvSeasonEpisodeNumber%2Cseries%7Btitle%7D%2ClastPubDate%7D%7D%7D",
            expected_results=5)

    def test_graphql_search_2(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bsearch%28searchParam%3A%22lief%22"
            "%2CprogramTypes%3A%5BSERIES%2CEPISODE%5D%2Climit%3A50%29%7Bitems%7B__typename"
            "%2Ctitle%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia"
            "%7Burl%2Clabel%7D%2Ctype%2Csources%7Btype%2Cfile%2Cdrm%7D%2CseasonNumber"
            "%2CtvSeasonEpisodeNumber%2Cseries%7Btitle%7D%2ClastPubDate%7D%7D%7D",
            expected_results=5)
