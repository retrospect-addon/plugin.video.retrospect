from typing import Optional, List

import xbmc

import xbmcplugin

from resources.lib import contenttype
from resources.lib.actions import action, keyword
from resources.lib.actions.actionparser import ActionParser
from resources.lib.actions.folderaction import FolderAction
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.chn_class import Channel
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.stopwatch import StopWatch
from resources.lib.logger import Logger
from resources.lib.mediaitem import FolderItem, MediaItem
from resources.lib.xbmcwrapper import XbmcWrapper


class SearchAction(FolderAction):
    def __init__(self, parameter_parser: ActionParser, channel: Channel, needle: Optional[str]):
        """Wraps the channel.process_folder_list

        :param parameter_parser:      A ActionParser object to is used to parse and create urls
        :param channel:               The channel info for the channel
        :needle:                      The needle

        """

        super().__init__(parameter_parser, channel)

        self.needle = needle if needle is None else HtmlEntityHelper.url_decode(needle)
        self.settings = AddonSettings.store(store_location=LOCAL)
        Logger.debug(f"Searching for: {self.needle}")

    def execute(self):
        # read the item from the parameters
        selected_item: MediaItem = self._media_item

        # determine the parent guid
        parent_guid = self.parameter_parser.get_parent_guid(self._channel, selected_item)

        if self.needle is None:
            self.__generate_search_history(selected_item, parent_guid)
            return

        elif not self.needle:
            # Search input
            needle = XbmcWrapper.show_key_board()
            if not needle:
                xbmcplugin.endOfDirectory(self.handle, False, cacheToDisc=True)
                return

            # noinspection PyTypeChecker
            history: List[str] = self.settings.get_setting("search", self._channel, [])
            history = list(set([needle] + history))
            self.settings.set_setting("search", history[0:10], self._channel)

            # Make sure we actually load a new URL so a refresh won't pop up a loading screen.
            needle = HtmlEntityHelper.url_encode(needle)
            xbmcplugin.endOfDirectory(self.handle, True, cacheToDisc=True)
            url = self.parameter_parser.create_action_url(self._channel, action.SEARCH, needle=needle)
            xbmc.executebuiltin(f"Container.Update({url})")

        else:
            watcher = StopWatch("Plugin processing Search Request", Logger.instance())
            media_items = self._channel.search_site(needle=self.needle)
            self._generate_kodi_items(media_items, parent_guid, selected_item, watcher)

    def __generate_search_history(self, selected_item: MediaItem, parent_guid: str):
        watcher = StopWatch("Plugin processing Search History", Logger.instance())

        # noinspection PyTypeChecker
        history: List[str] = self.settings.get_setting("search", self._channel, [])

        media_items = []
        search_item = FolderItem(
            f"\b{LanguageHelper.get_localized_string(LanguageHelper.NewSearch)}",
            f"{self._channel.search_url}&{keyword.NEEDLE}=",
            content_type=contenttype.VIDEOS
        )
        media_items.append(search_item)

        for needle in history:
            encoded_needle = HtmlEntityHelper.url_encode(needle)
            url = self.parameter_parser.create_action_url(self._channel, action.SEARCH,
                                                          needle=encoded_needle)
            item = FolderItem(needle, url, content_type=contenttype.VIDEOS)
            media_items.append(item)

        self._generate_kodi_items(media_items, parent_guid, selected_item, watcher)
