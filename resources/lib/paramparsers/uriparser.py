# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.paramparsers.parameter import Parameter
from resources.lib.paramparsers.paramparser import ParamParser

# The main URL mapping if parameters
URL_MAP = {
    Parameter.ACTION: 0,
    Parameter.CHANNEL: 1,
    Parameter.CHANNEL_CODE: 2,
    Parameter.PICKLE: 3
}


class UriParser(ParamParser):
    def __init__(self, url, addon_name=None):
        """ Creates a base ParamParser object.

        :param str url:         The url to parse
        :param str addon_name:  The add-on plugin-uri (the plugin://....) part

        """

        Logger.trace("%s + %s", addon_name, url)
        super(UriParser, self).__init__()

        # Kodi does not split the path from the add-on part. It eithers comes via the
        # the add-on name (plugin) or via the url (menu call)
        if addon_name:
            url_parts = addon_name.split("/", 3)
        else:
            url_parts = url.split("/", 3)

        # determine the query parameters
        self._pluginName = "{}//{}/".format(url_parts[0], url_parts[2])
        self._params = dict()
        self._url = url_parts[3]

    def parse_url(self):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None|MediaItem]

        """

        Logger.debug("Parsing uri parameters from: %s%s", self._pluginName,  self._url)

        self._params = dict()
        if self._url == '':
            return self._params

        params = self._url.split("/")
        params_count = len(params)
        for param, param_idx in URL_MAP.items():
            # if the index is higher than the parameter count, stop
            if param_idx >= params_count:
                continue

            self._params[param] = params[param_idx] or None

        # If there was an item, de-pickle it
        pickle = self._params.get(Parameter.PICKLE)
        if pickle:
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

        if not action:
            raise ValueError("Cannot create URL without 'action'")

        params = [""] * len(URL_MAP)
        if channel:
            params[URL_MAP[Parameter.CHANNEL]] = channel.moduleName
            if channel.channelCode:
                params[URL_MAP[Parameter.CHANNEL_CODE]] = channel.channelCode

        params[URL_MAP[Parameter.ACTION]] = action

        if item is not None:
            pickle = self._pickler.pickle_media_item(item)
            params[URL_MAP[Parameter.PICKLE]] = pickle

        # Create an url, but remove the empty ending uri parts
        url = "{}{}".format(self._pluginName, "/".join(params)).rstrip("/")
        return url

    def __str__(self):
        return "Uri-{}".format(super(UriParser, self).__str__())
