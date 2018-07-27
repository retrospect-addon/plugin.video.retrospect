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

    def set_setting(self, setting_id, setting_value, channel=None):
        pass

    def get_boolean_setting(self, setting_id, channel=None, default=None):
        pass

    def get_integer_setting(self, setting_id, channel=None, default=None):
        pass

    def get_setting(self, setting_id, channel=None, default=None):
        pass

    def get_localized_string(self, string_id):
        pass

    def open_settings(self):
        pass

    def __del__(self):
        pass
