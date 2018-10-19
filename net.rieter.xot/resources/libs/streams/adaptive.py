#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from helpers.htmlentityhelper import HtmlEntityHelper


class Adaptive:

    def __init__(self):
        pass

    @staticmethod
    def get_license_key(key_url, key_type="R", key_headers=None, key_value=None):
        """ Generates a propery license key value

        # A{SSM} -> not implemented
        # R{SSM} -> raw format
        # B{SSM} -> base64 format
        # D{SSM} -> decimal format

        The generic format for a LicenseKey is:
        |<url>|<headers>|<key with placeholders|

        The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

        @type key_url: str
        @param key_url: the URL where the license key can be obtained

        @type key_type: str
        @param key_type: the key type (A, R, B or D)

        @type key_headers: dict
        @param key_headers: A dictionary that contains the HTTP headers to pass

        @type key_value: str
        @param key_value: i
        @return:
        """

        header = ""
        if key_headers:
            for k, v in list(key_headers.items()):
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.url_encode(v))

        if key_type in ("A", "R", "B"):
            key_value = "{0}{{SSM}}".format(key_type)
        elif key_type == "D":
            if "D{SSM}" not in key_value:
                raise ValueError("Missing D{SSM} placeholder")
            key_value = HtmlEntityHelper.url_encode(key_value)

        return "{0}|{1}|{2}|".format(key_url, header.strip("&"), key_value)

    # noinspection PyUnusedLocal
    @staticmethod
    def set_input_stream_addon_input(strm, proxy=None, headers=None, addon="inputstream.adaptive",
                                     manifest_type=None,
                                     license_key=None,
                                     license_type=None,
                                     max_bit_rate=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        @param license_key:
        @param license_type:
        @param addon:             (string) Adaptive add-on to use
        @param manifest_type:      (string) Type of manifest (hls/mpd)
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening
        @param strm:              (MediaStream) the MediaStream to update
        @param int max_bit_rate:    The maximum bitrate to use (optional)

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            stream = part.AppendMediaStream(m3u8url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        """

        if manifest_type is None:
            raise ValueError("No manifest type set")

        strm.Adaptive = True

        # See https://github.com/peak3d/inputstream.adaptive/blob/master/inputstream.adaptive/addon.xml.in
        strm.AddProperty("inputstreamaddon", addon)
        strm.AddProperty("inputstream.adaptive.manifest_type", manifest_type)
        if license_key:
            strm.AddProperty("inputstream.adaptive.license_key", license_key)
        if license_type:
            strm.AddProperty("inputstream.adaptive.license_type", license_type)
        if max_bit_rate:
            strm.AddProperty("inputstream.adaptive.max_bandwidth", max_bit_rate * 1000)

        if headers:
            header = ""
            for k, v in list(headers.items()):
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.url_encode(v))
            strm.AddProperty("inputstream.adaptive.stream_headers", header.strip("&"))

        return strm

    @staticmethod
    def set_max_bitrate(stream, max_bit_rate):
        if not stream.Adaptive or max_bit_rate == 0:
            return

        # Previously defined when creating the stream => We don't override that
        if "inputstream.adaptive.max_bandwidth" in stream.Properties:
            return

        stream.AddProperty("inputstream.adaptive.max_bandwidth", str(max_bit_rate * 1000))
        return
