# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestSrfChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestSrfChannel, self).__init__(methodName, "channel.de.srf", "srf")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_show_listing(self):
        url = "https://www.srf.ch/play/v3/api/srf/production/videos-by-show-id?showId=c6a639e7-97a0-0001-5112-19c512b01474"
        self._test_folder_url(url, expected_results=4)

    def test_video_update(self):
        url = "https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:srf:video:28af922c-92a9-48b4-8d9c-35ba3a327620.json?onlyChapters=false&vector=portalplay"
        self._test_video_url(url)

    def test_live_channels(self):
        url = "https://www.srf.ch/play/v3/api/srf/production/tv-livestreams-now-and-next"
        self._test_folder_url(url, expected_results=2)

    def test_update_live_channel(self):
        url = "https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/urn:srf:video:c4927fcf-e1a0-0001-7edd-1ef01d441651.json?onlyChapters=false&vector=portalplay"
        self._test_video_url(url)
