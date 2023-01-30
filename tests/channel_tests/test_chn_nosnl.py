# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestNosChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNosChannel, self).__init__(methodName, "channel.nos.nosnl", "nosnl")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 4, "No items found in mainlist")

    # def test_most_viewed_items(self):
    #     url = "https://api.nos.nl/mobile/videos/most-viewed/phone.json"
    #     self._test_folder_url(url, expected_results=10)

    def test_video_update(self):
        url = "https://api.nos.nl/mobile/video/2380242/phone.json"
        from resources.lib.mediaitem import MediaItem
        item = self._test_video_url(url)    # type: MediaItem

        for stream in [s for s in item.streams if "hls" in s.Url]:
            self.assertTrue("cdn.streamgate.nl" in stream.Url)

    def test_resolver_update(self):
        url = "https://resolver.streaming.api.nos.nl/stream?stream=nos-event1&profile=hls_unencrypted&policy=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjb3JlLm5vcy5ubCIsInN1YiI6Im5vcy1ldmVudDEiLCJhdWQiOlsicmVzb2x2ZXIuc3RyZWFtaW5nLmFwaS5ub3MubmwiXSwiaWF0IjoxNjI3NDEzMjYzLCJhbGxvd2VkQXJlYXMiOlsiTkwiXSwiaXNHZW9wcm90ZWN0ZWQiOnRydWV9.4-I5yu9hcfJE37CdPVkWf4q7kDlEGTYUNVEM8stctV8"
        url = "https://resolver.streaming.api.nos.nl/stream?stream=nos-npo-2&profile=hls_unencrypted&policy=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjb3JlLm5vcy5ubCIsInN1YiI6Im5vcy1ucG8tMiIsImF1ZCI6WyJyZXNvbHZlci5zdHJlYW1pbmcuYXBpLm5vcy5ubCJdLCJpYXQiOjE2NzUxMTAzNTQsImFsbG93ZWRBcmVhcyI6WyJOTCIsIkFXIiwiQ1ciLCJTWCIsIkJRIl0sImlzR2VvcHJvdGVjdGVkIjp0cnVlfQ.KPRYyZ1hde_lohz-5joacR3YwJljU0vr-Aqr7S_aqWk"
        item = self._test_video_url(url)
        for stream in [s for s in item.streams if "hls" in s.Url]:
            self.assertTrue(".streamgate." in stream.Url)
