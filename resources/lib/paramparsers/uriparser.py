# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.mediaitem import MediaItem
from resources.lib.paramparsers.paramparser import ParamParser


class UriParser(ParamParser):
    def __init__(self, addon_name, url):
        """ Creates a base ParamParser object.

        :param str addon_name:  The name of the add-on
        :param str url:         The url to parse

        """

        super(UriParser, self).__init__(addon_name, url)

    def parse_url(self):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None|MediaItem]

        """

        raise NotImplementedError

    def _create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        :param ChannelInfo|Channel|None channel:    The channel object to use for the URL.
        :param str action:                          Action to create an url for
        :param MediaItem item:                      The media item to add
        :param str category:                        The category to use.

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        raise NotImplementedError

    def __str__(self):
        return "Uri-{}".format(super(UriParser, self).__str__())
