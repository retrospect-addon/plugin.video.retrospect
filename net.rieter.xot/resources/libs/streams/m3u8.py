#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
from urihandler import UriHandler
from logger import Logger
from regexer import Regexer


class M3u8:
    def __init__(self):
        pass

    @staticmethod
    def GetStreamsFromM3u8(url, proxy=None, headers=None, appendQueryString=False):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening
        @param url:               (String) The url to download
        @param appendQueryString: (boolean) should the existing query string be appended?

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

        qs = None
        if appendQueryString and "?" in url:
            base, qs = url.split("?", 1)
            Logger.Info("Going to append QS: %s", qs)

        Logger.Debug("Processing M3U8 Streams: %s", url)
        needle = "BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
        needles = Regexer.DoRegex(needle, data)

        baseUrlLogged = False
        baseUrl = url[:url.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.Trace(n)
            if "://" not in n[1]:
                if not baseUrlLogged:
                    Logger.Debug("Using baseUrl %s for M3u8", baseUrl)
                    baseUrlLogged = True
                stream = "%s/%s" % (baseUrl, n[1])
            else:
                if not baseUrlLogged:
                    Logger.Debug("Full url found in M3u8")
                    baseUrlLogged = True
                stream = n[1]
            bitrate = n[0]

            if qs is not None and stream.endswith("?null="):
                stream = stream.replace("?null=", "?%s" % (qs, ))
            elif qs is not None:
                stream = "%s?%s" % (stream, qs)
            streams.append((stream, bitrate))

        Logger.Debug("Found %s substreams in M3U8", len(streams))
        return streams

if __name__ == "__main__":
    from debug.initdebug import DebugInitializer
    DebugInitializer()

    # url = "http://tv4play-i.akamaihd.net/i/mp4root/2014-01-27/Bingolotto2601_2534830_,T6MP43,T6MP48,T6MP415,_.mp4.csmil/master.m3u8"
    # url = "http://iphone.streampower.be/een_nogeo/_definst_/2013/08/1000_130830_placetobe_marjolein_Website_Een_M4V.m4v/playlist.m3u8"
    # url = "http://iphone.cdn.viasat.tv/iphone/001/00104/V10427_16andpregnant_xn7qthrkj0heoqgq_iphone.m3u8"  # has only a bitrate
    url = "http://livestreams.omroep.nl/live/npo/regionaal/rtvnoord2/rtvnoord2.isml/rtvnoord2.m3u8?protection=url"  # appendQueryString
    results = M3u8.GetStreamsFromM3u8(url, DebugInitializer.Proxy, appendQueryString=True)
    results.sort(lambda x, y: cmp(int(x[1]), int(y[1])))
    for s, b in results:
        if s.count("://") > 1:
            raise Exception("Duplicate protocol in url: %s", s)
        print "%s - %s" % (b, s)
        Logger.Info("%s - %s", b, s)

    Logger.Instance().CloseLog()
