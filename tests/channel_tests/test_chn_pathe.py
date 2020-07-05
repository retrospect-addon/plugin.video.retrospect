# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import datetime

from tests.channel_tests.channeltest import ChannelTest


class TestPatheChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestPatheChannel, self).__init__(methodName, "channel.videos.pathenl", "pathejson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 10, "No items found in mainlist")

    def test_tomorrows_trailers(self):
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://connect.pathe.nl/v1/cinemas/7/schedules?date={0:04d}-{1:02d}-{2:02d}".format(
            tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=10)

    def test_now_playing(self):
        url = "https://connect.pathe.nl/v1/cinemas/7/movies/nowplaying"
        self._test_folder_url(url, expected_results=10)
