# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.mediaitem import MediaItem
from resources.lib.pickler import Pickler


class ParamParser(object):
    def __init__(self, addon_name):
        """ Creates a base ParamParser object.

        :param str addon_name:  The name of the add-on

        """

        # determine the query parameters
        self.pluginName = addon_name

        # We need a picker for this instance
        self._pickler = Pickler()

    def create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        :param ChannelInfo|Channel channel:     The channel object to use for the URL.
        :param str action:                      Action to create an url for
        :param MediaItem item:                  The media item to add
        :param str category:                    The category to use.

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        raise NotImplementedError

    def parse_url(self, url):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        :param str url:     The url to parse

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None]

        """

        raise NotImplementedError
