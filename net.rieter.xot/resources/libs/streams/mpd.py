# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

from streams.adaptive import Adaptive


class Mpd:
    def __init__(self):
        pass

    @staticmethod
    def set_input_stream_addon_input(strm, proxy=None, headers=None,
                                     license_key=None, license_type="com.widevine.alpha",
                                     max_bit_rate=None,
                                     persist_storage=False,
                                     service_certificate=None):

        return Adaptive.set_input_stream_addon_input(strm, proxy, headers,
                                                     manifest_type="mpd",
                                                     license_key=license_key,
                                                     license_type=license_type,
                                                     max_bit_rate=max_bit_rate,
                                                     persist_storage=persist_storage,
                                                     service_certificate=service_certificate)

    @staticmethod
    def get_license_key(key_url, key_type="R", key_headers=None, key_value=None):
        # type: (str, str, dict, str) -> str

        return Adaptive.get_license_key(key_url,
                                        key_type=key_type,
                                        key_headers=key_headers,
                                        key_value=key_value)
