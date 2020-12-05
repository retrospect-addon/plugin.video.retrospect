# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import os
import unittest

from . channeltest import ChannelTest


class TestTv4Channel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestTv4Channel, self).__init__(methodName, "channel.se.tv4se", "tv4segroup")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 7, "Incorrect number of items in mainlist")

    def test_tv_show_list(self):
        url = "https://www.tv4play.se/_next/data/ss-4G6Rv-ZEyGL978Ro6Z/allprograms.json"
        # Don't use the the GraphQL for now.
        # url = "https://graphql.tv4play.se/graphql?query=query%7BprogramSearch%28per_page%3A1000%29%7B__typename%2Cprograms%7B__typename%2Cdescription%2CdisplayCategory%2Cid%2Cimage%2Cimages%7Bmain16x9%7D%2Cname%2Cnid%2Cgenres%2CvideoPanels%7Bid%2Cname%7D%7D%2CtotalHits%7D%7D"
        self._test_folder_url(url, expected_results=100)

    def test_category_list(self):
        url = "https://graphql.tv4play.se/graphql?query=query%7Btags%7D"
        self._test_folder_url(url, expected_results=5)

    def test_category_tv_show_list(self):
        url = "https://graphql.tv4play.se/graphql?query=query%7BprogramSearch%28tag%3A%22Humor%22%2Cper_page%3A1000%29%7B__typename%2Cprograms%7B__typename%2Cdescription%2CdisplayCategory%2Cid%2Cimage%2Cimages%7Bmain16x9%7D%2Cname%2Cnid%2Cgenres%2CvideoPanels%7Bid%2Cname%7D%7D%2CtotalHits%7D%7D"
        self._test_folder_url(url, expected_results=20)

    @unittest.skip("Currenlty not available")
    def test_recents(self):
        url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet&per_page=32&is_live=true&product_groups=2&type=episode&per_page=100"
        self._test_folder_url(url, expected_results=2)

    @unittest.skip("Currenlty not available")
    def test_popular(self):
        url = "https://api.tv4play.se/play/video_assets/most_viewed?type=episode&platform=tablet&is_live=false&per_page=100&start=0"
        self._test_folder_url(url, expected_results=5)

    @unittest.skip("Currenlty not available")
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
        self.assertEqual(yesterday.day, items[1]._MediaItem__timestamp.day)
        self.assertEqual(yesterday.month, items[1]._MediaItem__timestamp.month)
        self.assertEqual(yesterday.year, items[1]._MediaItem__timestamp.year)

    @unittest.skip("Currenlty not available")
    def test_tv_show_videos(self):
        url = "https://api.tv4play.se/play/video_assets?platform=tablet&per_page=100&is_live=false&type=episode&page=1&node_nids=nyheterna&start=0"
        self._test_folder_url(url, expected_results=5)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_playback(self):
        url = "https://playback-api.b17g.net/media/13281470?service=tv4&device=browser&protocol=dash"
        self._test_video_url(url)

    @unittest.skip("Currenlty not available")
    def test_tv4_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv4se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv4se", chn.channelCode)

    @unittest.skip("Currenlty not available")
    def test_sjuan_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv7se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv7se", chn.channelCode)

    @unittest.skip("Currenlty not available")
    def test_tv12_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "tv12se")
        self.assertIsNotNone(chn)
        self.assertEqual("tv12se", chn.channelCode)

    @unittest.skip("Currenlty not available")
    def test_tv4_main_list(self):
        url = "https://api.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000&fl=nid,name,program_image,is_premium,updated_at,channel&start=0"
        self._test_folder_url(url, expected_results=50)

    def test_tv4play_graph_video_list(self):
        url = "https://graphql.tv4play.se/graphql?query=%7BvideoPanel%28id%3A%20%226xCXrYiuiC2lSqs6jfIZIM%22%29%7Bname%2CvideoList%28limit%3A%20100%29%7BtotalHits%2CvideoAssets%7Btitle%2Cid%2Cdescription%2Cseason%2Cepisode%2CdaysLeftInService%2CbroadcastDateTime%2Cimage%2Cfreemium%2CdrmProtected%2Clive%2Cduration%7D%7D%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_list_with_seasons_folders(self):
        url = "https://graphql.tv4play.se/graphql?query=%7Bprogram%28nid%3A%22intelligence%22%29%7Bname%2Cdescription%2CvideoPanels%7Bid%2Cname%2Csubheading%2CassetType%7D%7D%7D"
        self._test_folder_url(url, expected_results=1)
