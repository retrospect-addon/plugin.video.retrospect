# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from tests.channel_tests.channeltest import ChannelTest


class TestUrPlayChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestUrPlayChannel, self).__init__(methodName, "channel.se.urplay", None)

    def test_video_play(self):
        url = "https://urplay.se/program/218054-lilla-aktuellt-skola-2020-10-16"
        self._test_video_url(url)

    def test_video_audio(self):
        url = "https://urplay.se/program/216777-ajatuksia-suomeksi-unelmaelama"
        self._test_video_url(url)
