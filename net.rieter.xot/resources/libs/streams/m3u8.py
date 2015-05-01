__author__ = 'Bas'

from urihandler import UriHandler
from logger import Logger
from regexer import Regexer


class M3u8:
    def __init__(self):
        pass

    @staticmethod
    def GetStreamsFromM3u8(url, proxy=None, headers=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that can be used by
        other methods

        @type headers: dict   - Possible HTTP Headers
        @param proxy:  Proxy  - The proxy to use for opening
        @param url:    String - The url to download

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        streams = []

        data = UriHandler.Open(url, proxy, additionalHeaders=headers)
        Logger.Trace(data)
        Logger.Debug("Processing M3U8 Streams: %s", url)
        needle = "BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
        needles = Regexer.DoRegex(needle, data)

        baseUrlLogged = False
        baseUrl = url[:url.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.Trace(n)
            if not "://" in n[1]:
                if not baseUrlLogged:
                    Logger.Trace("Using baseUrl %s for M3u8", baseUrl)
                    baseUrlLogged = True
                stream = "%s/%s" % (baseUrl, n[1])
            else:
                if not baseUrlLogged:
                    Logger.Trace("Full url found in M3u8")
                    baseUrlLogged = True
                stream = n[1]
            bitrate = n[0]
            streams.append((stream, bitrate))

        Logger.Debug("Found %s substreams in M3U8", len(streams))
        return streams

if __name__ == "__main__":
    from debug.initdebug import DebugInitializer
    DebugInitializer()

    #url = "http://l24m4813963ddb0052ec084b000000.b120d95db771e206.adaptive-e50c1b.npostreaming.nl/lmshieldv2/3/nps/rest/2014/NPS_1237113/NPS_1237113.ism/NPS_1237113.m3u8"
    #url = "http://manifest.us.rtl.nl/rtlxl/network/pc/adaptive/components/videorecorder/30/301504/301505/80619c50-3e01-39a5-b51e-1d52b7526ea1.ssm/80619c50-3e01-39a5-b51e-1d52b7526ea1.m3u8"
    #url = "http://manifest.us.rtl.nl/rtlxl/network/ipad/adaptive/components/gezondheid/rtlgezond/4me/304422/a747f699-74ad-3178-9690-313fa4ea0128.ssm/a747f699-74ad-3178-9690-313fa4ea0128.m3u8"
    #url = "http://svtplay10m-f.akamaihd.net/i/world/open/20140126/1361888-003A_TEXT/AGENDA-003A-text-7331e3182439635d_,900,348,564,1680,2800,.mp4.csmil/master.m3u8"
    #url = "https://svt11hls-lh.akamaihd.net/i/svt11hls_0@78143/master.m3u8?__b__=563"
    #url = "http://tv4play-i.akamaihd.net/i/mp4root/2014-01-27/Bingolotto2601_2534830_,T6MP43,T6MP48,T6MP415,_.mp4.csmil/master.m3u8"
    #url = "http://iphone.streampower.be/een_nogeo/_definst_/2013/08/1000_130830_placetobe_marjolein_Website_Een_M4V.m4v/playlist.m3u8"
    url = "http://iphone.cdn.viasat.tv/iphone/001/00104/V10427_16andpregnant_xn7qthrkj0heoqgq_iphone.m3u8"  # has only a bitrate
    results = M3u8.GetStreamsFromM3u8(url, DebugInitializer.Proxy)
    results.sort(lambda x, y: cmp(int(x[1]), int(y[1])))
    for s, b in results:
        if s.count("://") > 1:
            raise Exception("Duplicate protocol in url: %s", s)
        print "%s - %s" % (b, s)
        Logger.Info("%s - %s", b, s)

    Logger.Instance().CloseLog()