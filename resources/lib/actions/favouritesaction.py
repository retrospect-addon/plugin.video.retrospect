# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.actions.addonaction import AddonAction
from resources.lib.actions.folderaction import FolderAction
from resources.lib.channelinfo import ChannelInfo
from resources.lib.logger import Logger
from resources.lib.paramparser import ParameterParser
from resources.lib.retroconfig import Config


class ShowFavouritesAction(AddonAction):
    def __init__(self, parameter_parser, channel_object=None):
        """

        :param ParameterParser parameter_parser:  a ParameterParser object to is used to parse and
                                                   create urls
        :param ChannelInfo|None channel_object:   The channel to show favourites for.
                                                   Might be None to show all.

        """

        super(ShowFavouritesAction, self).__init__(parameter_parser)
        self.__channel = channel_object

    def execute(self):
        """ Show the favourites (for a channel). """

        Logger.debug("Plugin::show_favourites")

        if self.__channel is None:
            Logger.info("Showing all favourites")
        else:
            Logger.info("Showing favourites for: %s", self.__channel)

        # Local import for performance
        from resources.lib.favourites import Favourites
        f = Favourites(Config.favouriteDir)
        favs = f.list(self.__channel)

        # Execute the process folder action
        sub_action = FolderAction(
            parameter_parser=self.parameter_parser,
            channel=self.__channel,
            favorites=favs
        )
        sub_action.execute()
