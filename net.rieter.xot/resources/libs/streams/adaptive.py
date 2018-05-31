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
    def SetInputStreamAddonInput(strm, proxy=None, headers=None, addon="inputstream.adaptive",
                                 manifestType=None,
                                 licenseKey=None,
                                 licenseType=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        @param licenseKey:
        @param licenseType:
        @param addon:             (string) Adaptive add-on to use
        @param manifestType:      (string) Type of manifest (hls/mpd)
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening
        @param strm:              (MediaStream) the MediaStream to update

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            stream = part.AppendMediaStream(m3u8url, 0)
            M3u8.SetInputStreamAddonInput(stream, self.proxy, self.headers)

        """

        if manifestType is None:
            raise ValueError("No manifest type set")

        strm.AddProperty("inputstreamaddon", addon)
        strm.AddProperty("inputstream.adaptive.manifest_type", manifestType)
        if licenseKey:
            strm.AddProperty("inputstream.adaptive.license_key", licenseKey)
        if licenseType:
            strm.AddProperty("inputstream.adaptive.license_type", licenseType)

        if headers:
            header = ""
            for k, v in list(headers.items()):
                header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.UrlEncode(v))
            strm.AddProperty("inputstream.adaptive.stream_headers", header.strip("&"))

        return strm
