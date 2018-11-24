#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================


class SettingsStore(object):
    def __init__(self, logger):
        if not logger:
            raise ValueError("Missing logger")

        self._logger = logger
        # What settings should we not expose via the logger?
        self._secure_setting_ids = ["application_key", "client_id"]

    def set_setting(self, setting_id, setting_value, channel=None):
        pass

    def get_boolean_setting(self, setting_id, channel=None, default=None):
        """ Returns a boolean value for the given setting_id.

        :param str setting_id:  The ID of the setting that is to be retrieved.
        :param channel:         If specified the specific channel setting is retrieved.
        :param bool default:    The default value in case the settings is not set yet.

        :returns: the boolean value for the given setting_id
        :rtype: bool

        """
        pass

    def get_integer_setting(self, setting_id, channel=None, default=None):
        """ Returns an interger value for the given setting_id.

        :param str setting_id:  The ID of the setting that is to be retrieved.
        :param channel:         If specified the specific channel setting is retrieved.
        :param int default:     The default value in case the settings is not set yet.

        :returns: the integer value for the given setting_id
        :rtype: int

        """
        pass

    def get_setting(self, setting_id, channel=None, default=None):
        pass

    def get_localized_string(self, string_id):
        pass

    def open_settings(self):
        pass

    def _get_safe_print_value(self, setting_id, setting_value):
        if setting_id in self._secure_setting_ids:
            return "<no of your business>"
        return setting_value

    def __del__(self):
        pass
