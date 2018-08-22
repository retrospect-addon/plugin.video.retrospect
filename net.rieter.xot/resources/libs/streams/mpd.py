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
        return Adaptive.GetLicenseKey(keyUrl, keyType=keyType, keyHeaders=keyHeaders)
