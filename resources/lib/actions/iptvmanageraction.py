# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.logger import Logger
from resources.lib.actions.actionparser import ActionParser


class IPTVManagerAction(AddonAction):
    def __init__(self, parameter_parser, request, port):
        """ Sending channel and EPG data to IPTV Manager

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param string request:          The data to query [channels, epg]
        :param integer port:            The port number to communicate with IPTV Manager

        """

        super(IPTVManagerAction, self).__init__(parameter_parser)

        self.__request = request
        self.__port = port

    def execute(self):
        """ Send the output of the wrappers to socket """

        Logger.debug("Execute IPTVManagerAction")
