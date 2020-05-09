# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from tests.channel_tests.channeltest import ChannelTest


class TestSvtChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestSvtChannel, self).__init__(methodName, "channel.se.svt", "svt")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 10, "No items found in mainlist")

    def test_main_program_list(self):
        self._test_folder_url(
            "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&"
            "operationName=GridPage&variables=%7B%22selectionId%22%3A%20%22latest%22%7D&extensions="
            "%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20"
            "%22265677a2465d93d39b536545cdc3664d97e3843ce5e34f145b2a45813b85007b%22%7D%7D", 7)

    def test_video_list(self):
        self._test_folder_url(
            "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&operation"
            "Name=GridPage&variables=%7B%22selectionId%22%3A%20%22popular%22%7D&extensions=%7B%22"
            "persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22265677"
            "a2465d93d39b536545cdc3664d97e3843ce5e34f145b2a45813b85007b%22%7D%7D", 5)
