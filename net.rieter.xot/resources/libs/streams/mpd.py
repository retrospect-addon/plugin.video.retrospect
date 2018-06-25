from helpers.htmlentityhelper import HtmlEntityHelper
from streams.adaptive import Adaptive


class Mpd:
    def __init__(self):
        pass

    @staticmethod
    def SetInputStreamAddonInput(strm, proxy=None, headers=None,
                                 licenseKey=None, licenseType="com.widevine.alpha"):

        return Adaptive.SetInputStreamAddonInput(strm, proxy, headers,
                                                 manifestType="mpd",
                                                 licenseKey=licenseKey,
                                                 licenseType=licenseType)

    @staticmethod
    def GetLicenseKey(keyUrl, keyType="R", keyHeaders=None):

        # A{SSM} -> not implemented
        # R{SSM} -> raw
        # B{SSM} -> base64

        header = ""
        for k, v in list(keyHeaders.items() or {}):
            header = "{0}&{1}={2}".format(header, k, HtmlEntityHelper.UrlEncode(v))

        return "{0}|{1}|{2}{{SSM}}|".format(keyUrl, header.strip("&"), keyType)
