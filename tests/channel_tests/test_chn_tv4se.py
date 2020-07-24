# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import datetime
import os
import unittest

from tests.channel_tests.channeltest import ChannelTest


class TestTv4Channel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestTv4Channel, self).__init__(methodName, "channel.se.tv4se", "tv4segroup")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 12, "Incorrect number of items in mainlist")

    def test_tv_show_list(self):
        url = "https://graphql.tv4play.se/graphql?query=query%7BprogramSearch%28per_page%3A1000%29%7B__typename%2Cprograms%7B__typename%2Cdescription%2CdisplayCategory%2Cid%2Cimage%2Cimages%7Bmain16x9%7D%2Cname%2Cnid%2Cgenres%7D%2CtotalHits%7D%7D"
        self._test_folder_url(url, expected_results=100)

    def test_category_list(self):
        url = "https://graphql.tv4play.se/graphql?query=query%7Btags%7D"
        self._test_folder_url(url, expected_results=5)

    def test_category_tv_show_list(self):
        url = "https://graphql.tv4play.se/graphql?query=query%7BprogramSearch%28tag%3A%22Humor%22%2Cper_page%3A1000%29%7B__typename%2Cprograms%7B__typename%2Cdescription%2CdisplayCategory%2Cid%2Cimage%2Cimages%7Bmain16x9%7D%2Cname%2Cnid%2Cgenres%7D%2CtotalHits%7D%7D"
        self._test_folder_url(url, expected_results=25)

    def test_recents(self):
        url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet&per_page=32&is_live=true&product_groups=2&type=episode&per_page=100"
        self._test_folder_url(url, expected_results=5)

    def test_popular(self):
        url = "https://api.tv4play.se/play/video_assets/most_viewed?type=episode&platform=tablet&is_live=false&per_page=100&start=0"
        self._test_folder_url(url, expected_results=5)

    def test_yesterday(self):
        url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet" \
              "&is_live=false&product_groups=2&type=episode&per_page=100" \
              "&broadcast_from={:04d}{:02d}{:02d}" \
              "&broadcast_to={:04d}{:02d}{:02d}&"
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        url = url.format(yesterday.year, yesterday.month, yesterday.day, today.year, today.month, today.day)
        items = self._test_folder_url(url, expected_results=25)

        # Check the date
        self.assertEqual(yesterday.day, items[0]._MediaItem__timestamp.day)
        self.assertEqual(yesterday.month, items[0]._MediaItem__timestamp.month)
        self.assertEqual(yesterday.year, items[0]._MediaItem__timestamp.year)

    def test_tv_show_videos(self):
        url = "https://api.tv4play.se/play/video_assets?platform=tablet&per_page=100&is_live=false&type=episode&page=1&node_nids=nyheterna&start=0"
        self._test_folder_url(url, expected_results=5)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_playback(self):
        url = "https://playback-api.b17g.net/media/13281470?service=tv4&device=browser&protocol=dash"
        self._test_video_url(url)

    def test_tv4_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv4se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv4se", chn.channelCode)

    def test_sjuan_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv7se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv7se", chn.channelCode)

    def test_tv12_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv12se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv12se", chn.channelCode)

    def test_tv4_main_list(self):
        url = "https://api.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000&fl=nid,name,program_image,is_premium,updated_at,channel&start=0"
        self._test_folder_url(url, expected_results=50)
