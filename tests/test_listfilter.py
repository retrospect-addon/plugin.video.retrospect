import unittest

from tests.channel_tests.channeltest import ChannelTest


class TestListFilter(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestListFilter, self).__init__(methodName, "channel.nos.nos2010", "uzgjson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_no_filter(self):
        from resources.lib.addonsettings import AddonSettings
        from resources.lib.addonsettings import KODI
        AddonSettings.store(KODI).set_setting("geo_region", 0)
        AddonSettings.store(KODI).set_setting("hide_types", 0)

        items = self.__get_items()
        self.assertGreaterEqual(len(items), 2)

    def test_paid_filter_toggle(self):
        from resources.lib.addonsettings import AddonSettings
        from resources.lib.addonsettings import KODI

        AddonSettings.store(KODI).set_setting("hide_premium", "false")
        self.assertFalse(AddonSettings.store(KODI).get_boolean_setting("hide_premium"))
        AddonSettings.store(KODI).set_setting("hide_premium", "true")
        self.assertTrue(AddonSettings.store(KODI).get_boolean_setting("hide_premium"))

    def test_filter_list_paid(self):
        from resources.lib.addonsettings import AddonSettings
        from resources.lib.addonsettings import KODI
        AddonSettings.store(KODI).set_setting("hide_types", 0)
        AddonSettings.store(KODI).set_setting("hide_premium", "false")
        items = self.__get_items()
        all_items = len(items)

        AddonSettings.store(KODI).set_setting("hide_types", 0)
        AddonSettings.store(KODI).set_setting("hide_premium", "true")
        items = self.__get_items()
        self.assertLess(len(items), all_items)

    def tearDown(self):
        "Hook method for deconstructing the test fixture after testing it."
        from resources.lib.addonsettings import AddonSettings
        from resources.lib.addonsettings import KODI

        AddonSettings.store(KODI).set_setting("geo_region", 0)
        AddonSettings.store(KODI).set_setting("hide_types", 1)
        AddonSettings.store(KODI).set_setting("hide_premium", "false")

    def __get_items(self):
        items = self._test_folder_url(
            "https://npo.nl/start/api/domain/programs-by-season?guid=43eb0443-7ac8-4629-a7ed-b39ab65574b5",
            expected_results=1, retry=0)
        return items
