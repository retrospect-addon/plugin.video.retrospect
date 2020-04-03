# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.logger import Logger
from resources.lib.paramparser import ParameterParser


class ConfigureChannelAction(AddonAction):
    def __init__(self, parameter_parser, channel_info):
        """ Shows the current channels settings dialog.

        :param ParameterParser parameter_parser:  A ParameterParser object to is used to parse
                                                   and create urls
        :param ChannelInfo channel_info:          The channel info for the channel

        """

        super(ConfigureChannelAction, self).__init__(parameter_parser)

        self.__channel_info = channel_info

    def execute(self):
        """ Shows the current channels settings dialog. """

        if not self.__channel_info:
            Logger.warning("Cannot configure channel without channel info")

        Logger.info("Configuring channel: %s", self.__channel_info)
        AddonSettings.show_channel_settings(self.__channel_info)
