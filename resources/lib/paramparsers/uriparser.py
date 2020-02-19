# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel
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
    def __init__(self, add_on_id, add_on_path, query):
        """ Creates a base UriParser object.

        :param str add_on_id:    The id of the add-on
        :param str query:        The url to parse
        :param str add_on_path:  The add-on plugin-uri (the plugin://....) part

        """

        super(UriParser, self).__init__(add_on_id, add_on_path, query)
        raise NotImplementedError

    def parse_url(self):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None|MediaItem]

        """

        raise NotImplementedError

        # This does not work yet.
        # self._params = dict()
        # params = self._addon_path.split("/")
        # params_count = len(params)
        # for param, param_idx in URL_MAP.items():
        #     # if the index is higher than the parameter count, stop
        #     if param_idx >= params_count:
        #         continue
        #
        #     self._params[param] = params[param_idx] or None
        #
        # # If there was an item, de-pickle it
        # pickle = self._params.get(Parameter.PICKLE)
        # if pickle:
        #     self._params[Parameter.ITEM] = self._pickler.de_pickle_media_item(pickle)
        #
        # return self._params

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
        url = "plugin://{}/{}".format(self._addon_id, "/".join(params)).rstrip("/")
        return url

    def __str__(self):
        return "Uri-{}".format(super(UriParser, self).__str__())
