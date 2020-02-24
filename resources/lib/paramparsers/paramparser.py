# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from resources.lib.paramparsers.action import Action
from resources.lib.paramparsers.parameter import Parameter
from resources.lib.pickler import Pickler

from resources.lib.chn_class import Channel
from resources.lib.channelinfo import ChannelInfo
from resources.lib.mediaitem import MediaItem


# The main URL mapping if parameters.
URL_MAP = {
    Action.LIST_FOLDER: {
        Parameter.CHANNEL: 0,
        Parameter.CHANNEL_CODE: 1,
        Parameter.PICKLE: -2
    },
    Action.PLAY_VIDEO: {
        Parameter.CHANNEL: 0,
        Parameter.CHANNEL_CODE: 1,
        Parameter.PICKLE: 2,
    },
    Action.ALL_FAVOURITES: {},
    Action.LIST_CATEGORY: {
        Parameter.CATEGORY: 0,
    },
    Action.RESET_VAULT: {
        Parameter.SETTING_TAB_FOCUS: 0,
        Parameter.SETTING_SETTING_FOCUS: -1,
    },
    Action.SET_ENCRYPTION_PIN: {
        Parameter.SETTING_TAB_FOCUS: 0,
        Parameter.SETTING_SETTING_FOCUS: -1,
    },
    Action.SET_ENCRYPTED_VALUE: {
        Parameter.SETTING_ID: 0,
        Parameter.SETTING_NAME: 1,
        Parameter.SETTING_TAB_FOCUS: 2,
        Parameter.SETTING_SETTING_FOCUS: -3,
        Parameter.SETTING_ACTION_ID: -4,
    }
}


class ParamParser(object):
    def __init__(self, add_on_id, add_on_path, query):
        """ Creates a base ParamParser object.

        :param str add_on_id:    The id of the add-on
        :param str query:        The url to parse
        :param str add_on_path:  The add-on plugin-uri (the plugin://....) part

        """

        # determine the query parameters
        self._addon_path = add_on_path
        self._query = query
        self._addon_id = add_on_id

        # the resulting parameters
        self._params = dict()

        # We need a picker for this instance
        self._pickler = Pickler()

    def create_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        :param ChannelInfo|Channel|None channel:    The channel object to use for the URL.
        :param str action:                          Action to create an url for
        :param MediaItem item:                      The media item to add
        :param str category:                        The category to use.

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        # First do some initial and generic checks
        if action is None:
            raise Exception("action is required")

        # catch the plugin:// url's for items and channels.
        if item is not None and item.url and item.url.startswith("plugin://"):
            return item.url

        if item is None and channel is not None and channel.uses_external_addon:
            return channel.addonUrl

        # Then create a specific URL
        return self._create_url(channel, action, item, category)

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

    def _is_optional(self, action_config, parameter):
        """ Returns an indication whether the parameter is an optional one in the configuration.

        :param dict[string,int] action_config:  The configuration to use
        :param str parameter:                   The Parameter name to check

        :return: indication whether the parameters is an optional one

        Initially only the last of the configured parameters could be optional. Now more can be
        but it will not work if they are not the last ones.

        """
        # Check of optional parameters (negative IDX)
        idx = action_config[parameter]
        is_optional = idx < 0  # and len(action_config) == -idx + 1
        return is_optional

    def __str__(self):
        """ Returns a string representation of the current object."""

        str_dict = dict(self._params)
        if Parameter.ITEM in str_dict:
            del str_dict[Parameter.ITEM]

        full_url = "{}{}{}".format(self._addon_path, "?" if self._query else "", self._query)
        return "Plugin Params: {} ({})\n" \
               "Url:   {}\n" \
               "Path:  {}\n" \
               "Query: {}".format(str_dict, len(str_dict), full_url, self._addon_path, self._query or "<None>")
