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
    def GetLicenseKey(keyUrl, keyType="R", keyHeaders=None, keyValue=None):
        """ Generates a propery license key value

        # A{SSM} -> not implemented
        # R{SSM} -> raw format
        # B{SSM} -> base64 format
        # D{SSM} -> decimal format

        The generic format for a LicenseKey is:
        |<url>|<headers>|<key with placeholders|

        The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

        @type keyUrl: str
        @param keyUrl: the URL where the license key can be obtained

        @type keyType: str
        @param keyType: the key type (A, R, B or D)

        @type keyHeaders: dict
        @param keyHeaders: A dictionary that contains the HTTP headers to pass

        @type keyValue: str
        @param keyValue: i
        @return:
        """

        header = ""
        if keyHeaders:
            for k, v in list(keyHeaders.items()):
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.UrlEncode(v))

        if keyType in ("A", "R", "B"):
            keyValue = "{0}{{SSM}}".format(keyType)
        elif keyType == "D":
            if "D{SSM}" not in keyValue:
                raise ValueError("Missing D{SSM} placeholder")
            keyValue = HtmlEntityHelper.UrlEncode(keyValue)

        return "{0}|{1}|{2}|".format(keyUrl, header.strip("&"), keyValue)

    # noinspection PyUnusedLocal
    @staticmethod
    def SetInputStreamAddonInput(strm, proxy=None, headers=None, addon="inputstream.adaptive",
                                 manifestType=None,
                                 licenseKey=None,
                                 licenseType=None,
                                 maxBitRate=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        @param licenseKey:
        @param licenseType:
        @param addon:             (string) Adaptive add-on to use
        @param manifestType:      (string) Type of manifest (hls/mpd)
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening
        @param strm:              (MediaStream) the MediaStream to update
        @param int maxBitRate:    The maximum bitrate to use (optional)

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            stream = part.AppendMediaStream(m3u8url, 0)
            M3u8.SetInputStreamAddonInput(stream, self.proxy, self.headers)

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        """

        if manifestType is None:
            raise ValueError("No manifest type set")

        strm.Adaptive = True

        # See https://github.com/peak3d/inputstream.adaptive/blob/master/inputstream.adaptive/addon.xml.in
        strm.AddProperty("inputstreamaddon", addon)
        strm.AddProperty("inputstream.adaptive.manifest_type", manifestType)
        if licenseKey:
            strm.AddProperty("inputstream.adaptive.license_key", licenseKey)
        if licenseType:
            strm.AddProperty("inputstream.adaptive.license_type", licenseType)
        if maxBitRate:
            strm.AddProperty("inputstream.adaptive.max_bandwidth", maxBitRate * 1000)

        if headers:
            header = ""
            for k, v in list(headers.items()):
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.UrlEncode(v))
            strm.AddProperty("inputstream.adaptive.stream_headers", header.strip("&"))

        return strm

    @staticmethod
    def SetMaxBitrate(stream, maxBitRate):
        if not stream.Adaptive or maxBitRate == 0:
            return

        # Previously defined when creating the stream => We don't override that
        if "inputstream.adaptive.max_bandwidth" in stream.Properties:
            return

        stream.AddProperty("inputstream.adaptive.max_bandwidth", str(maxBitRate * 1000))
        return
