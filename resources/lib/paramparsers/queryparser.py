# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import random

from resources.lib.paramparsers.action import Action
from resources.lib.paramparsers.parameter import Parameter
from resources.lib.paramparsers.paramparser import ParamParser

from resources.lib.logger import Logger
from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.mediaitem import MediaItem


class QueryParser(ParamParser):
    def __init__(self, add_on_id, add_on_path, query):
        """ Creates a base QueryParser object.

        :param str add_on_id:    The id of the add-on
        :param str query:        The url to parse
        :param str add_on_path:  The add-on plugin-uri (the plugin://....) part

        """

        super(QueryParser, self).__init__(add_on_id, add_on_path, query.lstrip("?"))

    def parse_url(self):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        Note: If a pickled item was present, that item will be depickled.

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None|MediaItem]

        """

        self._params = dict()

        if self._query == '':
            return self._params

        try:
            for pair in self._query.split("&"):
                (k, v) = pair.split("=")
                self._params[k] = v

            # if the channelcode was empty, it was stripped, add it again.
            if Parameter.CHANNEL_CODE not in self._params:
                Logger.debug("Adding ChannelCode=None as it was missing from the dict: %s", self._params)
                self._params[Parameter.CHANNEL_CODE] = None
        except:
            Logger.critical("Cannot determine query strings from %s", self._query, exc_info=True)
            raise

        pickle = self._params.get(Parameter.PICKLE)
        if pickle:
            Logger.debug("Found Pickle: %s", pickle)
            self._params[Parameter.ITEM] = self._pickler.de_pickle_media_item(pickle)

        return self._params

    def _create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        :param ChannelInfo|Channel|None channel:    The channel object to use for the URL.
        :param str action:                          Action to create an url for
        :param MediaItem item:                      The media item to add
        :param str category:                        The category to use.

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        params = dict()
        if channel:
            params[Parameter.CHANNEL] = channel.moduleName
            if channel.channelCode:
                params[Parameter.CHANNEL_CODE] = channel.channelCode

        params[Parameter.ACTION] = action

        # it might have an item or not
        if item is not None:
            params[Parameter.PICKLE] = self._pickler.pickle_media_item(item)

            if action == Action.PLAY_VIDEO and item.isLive:
                params[Parameter.RANDOM_LIVE] = random.randint(10000, 99999)

        if category:
            params[Parameter.CATEGORY] = category

        url = "%s?" % (self._addon_path,)
        for k in params.keys():
            url = "%s%s=%s&" % (url, k, params[k])

        url = url.strip('&')
        # Logger.Trace("Created url: '%s'", url)
        return url

    def __str__(self):
        return "Query-{}".format(super(QueryParser, self).__str__())
