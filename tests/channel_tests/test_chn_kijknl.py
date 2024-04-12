# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

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

    @unittest.skip("Deprecated Embedded API")
    def test_update_embedded_mpd_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/vhlbVj34UM9?id=kijkapp&format=DASH&drm=CENC")

    @unittest.skip("Deprecated Embedded API")
    def test_update_embedded_mpd_encrypted_video(self):
        self._test_video_url(
            "https://embed.kijk.nl/api/video/P74c4ckPaE9?id=kijkapp&format=DASH&drm=CENC")

    def test_graphql_main_list(self):
        self._test_folder_url(
            "https://static.kijk.nl/all-series.json",
            expected_results=250
        )

    def test_graphql_multi_season_show(self):
        url = "https://graph.kijk.nl/graphql?query=query%7Bprograms%28guid%3A%22Ql03Io4n2Zi%22%29" \
              "%7Bitems%7BseriesTvSeasons%7Bid%2Ctitle%2CseasonNumber%2C__typename%7D%7D%7D%7D"
        self._test_folder_url(url, expected_results=3)

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

    def test_graphql_trending(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7BtrendingPrograms%7B__typename%2C"
            "title%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia%7Burl%2Clabel%7D%7D%7D",
            expected_results=3)

    def test_graphql_mpd_video(self):
        item = self._test_video_url(
            "https://api.prd.video.talpa.network/graphql?query=query%20sources(%24guid%3A%5BString"
            "%5D)%7Bprograms(guid%3A%24guid)%7Bitems%7Bguid%20sources%7Btype%20file%20drm%20"
            "__typename%7D%20tracks%7Bfile%20type%7D%20__typename%7D__typename%7D%7D&"
            "operationName=sources&variables=%7B%22guid%22%3A%22cdXgSQVNHwDoKy%22%7D")

        mpd = [s for s in item.streams if ".mpd" in s.Url]
        self.assertGreaterEqual(len(mpd), 1)
        self.assertEqual(len(mpd[0].Properties), 3)

    def test_graphql_m3u8_video(self):
        item = self._test_video_url(
            "https://api.prd.video.talpa.network/graphql?query=query%20sources(%24guid%3A%5BString"
            "%5D)%7Bprograms(guid%3A%24guid)%7Bitems%7Bguid%20sources%7Btype%20file%20drm%20"
            "__typename%7D%20tracks%7Bfile%20type%7D%20__typename%7D__typename%7D%7D&"
            "operationName=sources&variables=%7B%22guid%22%3A%22cdXgSQVNHwDoKy%22%7D")

        m3u8 = [s for s in item.streams if ".m3u8" in s.Url]
        self.assertGreaterEqual(len(m3u8), 1)

    def test_graphql_drm_video(self):
        item = self._test_video_url(
            "https://api.prd.video.talpa.network/graphql?query=query%20programs(%24guid%3A%5BString"
            "%5D%24limit%3AInt)%7Bprograms(guid%3A%24guid%20limit%3A%24limit)%7Bitems%7Bid%20"
            "guid%20availableRegion%20slug%20tvSeasonId%20sourceProgram%20type%20title%20sortTitle"
            "%20added%20publicationDateTime%20description%20longDescription%20shortDescription"
            "%20displayGenre%20tvSeasonEpisodeNumber%20seasonNumber%20seriesId%20duration%20series"
            "%7Bid%20guid%20slug%20title%20__typename%7Dmetadata%20...ImageMedia%20...Media%20..."
            "SeriesTvSeasons%20...Sources%20...Tracks%20...Ratings%20__typename%7D__typename%7D"
            "%7Dfragment%20Media%20on%20Program%7Bmedia%7BavailableDate%20availabilityState"
            "%20airedDateTime%20expirationDate%20type%20__typename%7D__typename%7Dfragment"
            "%20ImageMedia%20on%20Program%7BimageMedia%7Burl%20title%20label%20type"
            "%20__typename%7D__typename%7Dfragment%20SeriesTvSeasons%20on%20Program"
            "%7BseriesTvSeasons%7Bid%20guid%20title%20seasonNumber%20__typename%7D__typename"
            "%7Dfragment%20Sources%20on%20Program%7Bsources%7Btype%20file%20drm%20__typename"
            "%7D__typename%7Dfragment%20Tracks%20on%20Program%7Btracks%7Btype%20file%20kind"
            "%20label%20__typename%7D__typename%7Dfragment%20Ratings%20on%20Program"
            "%7Bratings%7Brating%20subRatings%20__typename%7D__typename"
            "%7D&operationName=programs&variables=%7B%22guid%22%3A%22dYhkgQM52Yy%22%7D")

        mpd = [s for s in item.streams if ".mpd" in s.Url]
        self.assertGreaterEqual(len(mpd), 1)
        self.assertEqual(len(mpd[0].Properties), 5)

    def test_graphql_search(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bsearch%28searchParam%3A%22veronica%22"
            "%2CprogramTypes%3A%5BSERIES%2CEPISODE%5D%2Climit%3A50%29%7Bitems%7B__typename"
            "%2Ctitle%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia"
            "%7Burl%2Clabel%7D%2Ctype%2Csources%7Btype%2Cfile%2Cdrm%7D%2CseasonNumber"
            "%2CtvSeasonEpisodeNumber%2Cseries%7Btitle%7D%2ClastPubDate%7D%7D%7D",
            expected_results=4)

    def test_graphql_search_2(self):
        self._test_folder_url(
            "https://graph.kijk.nl/graphql?query=query%7Bsearch%28searchParam%3A%22weg%22"
            "%2CprogramTypes%3A%5BSERIES%2CEPISODE%5D%2Climit%3A50%29%7Bitems%7B__typename"
            "%2Ctitle%2Cdescription%2Cguid%2Cupdated%2CseriesTvSeasons%7Bid%7D%2CimageMedia"
            "%7Burl%2Clabel%7D%2Ctype%2Csources%7Btype%2Cfile%2Cdrm%7D%2CseasonNumber"
            "%2CtvSeasonEpisodeNumber%2Cseries%7Btitle%7D%2ClastPubDate%7D%7D%7D",
            expected_results=5)

    def test_movies(self):
        url = "https://graph.kijk.nl/graphql?query=query%7Bprograms%28programTypes%3A%20MOVIE%29" \
              "%7BtotalResults%2Citems%7Btype%2C__typename%2Cguid%2Ctitle%2Cdescription%2C" \
              "duration%2CdisplayGenre%2CimageMedia%7Burl%2Clabel%7D%2CepgDate%2Csources%20%7B" \
              "type%2Cfile%2Cdrm%7D%2Ctracks%7Btype%2Ckind%2C%20label%2Cfile%7D%7D%7D%7D"
        self._test_folder_url(url, expected_results=5)
