from streams.adaptive import Adaptive


class Mpd:
    def __init__(self):
        pass

    @staticmethod
    def SetInputStreamAddonInput(strm, proxy=None, headers=None,
                                 licenseKey=None, licenseType="com.widevine.alpha"):

        # A{SSM} -> not implemented
        # R{SSM} -> raw
        # B{SSM} -> base64

        return Adaptive.SetInputStreamAddonInput(strm, proxy, headers,
                                                 manifestType="mpd",
                                                 licenseKey=licenseKey,
                                                 licenseType=licenseType)
