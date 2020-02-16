from resources.lib.logger import Logger
from resources.lib.paramparsers.paramparser import ParamParser

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.mediaitem import MediaItem


class UriParser(ParamParser):
    def __init__(self, addon_name, url):
        """ Creates a base ParamParser object.

        :param str addon_name:  The name of the add-on
        :param str url:         The url to parse

        """

        super(UriParser, self).__init__(addon_name, url)

    def create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        :param ChannelInfo|Channel|None channel:    The channel object to use for the URL.
        :param str action:                          Action to create an url for
        :param MediaItem item:                      The media item to add
        :param str category:                        The category to use.

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        raise NotImplementedError

    def parse_url(self):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None]

        """

        raise NotImplementedError
