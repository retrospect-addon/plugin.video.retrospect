from resources.lib.logger import Logger
from resources.lib.paramparsers.paramparser import ParamParser

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.mediaitem import MediaItem


class QueryParser(ParamParser):
    def __init__(self, addon_name):
        """ Creates a QueryParser object for parsing of pre 5.2 url's

            :param str addon_name:  The name of the add-on

        """
        super(QueryParser, self).__init__(addon_name)

    def create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action in the form of query parameters

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

        Logger.debug("Parsing parameters from: %s", url)

        raise NotImplementedError
