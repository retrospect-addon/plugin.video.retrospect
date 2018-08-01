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
from streams.adaptive import Adaptive


class M3u8:
    def __init__(self):
        pass

    @staticmethod
    def GetSubtitle(url, proxy=None, playListData=None, appendQueryString=True):
        data = playListData or UriHandler.Open(url, proxy)
        regex = '(#\w[^:]+)[^\n]+TYPE=SUBTITLES[^\n]*\W+URI="([^"]+.m3u8[^"\n\r]*)'
        sub = ""

        qs = None
        if appendQueryString and "?" in url:
            base, qs = url.split("?", 1)
            Logger.Info("Going to append QS: %s", qs)
        elif "?" in url:
            base, qs = url.split("?", 1)
            Logger.Info("Ignoring QS: %s", qs)
            qs = None
        else:
            base = url

        needles = Regexer.DoRegex(regex, data)
        URL_INDEX = 1
        baseUrlLogged = False
        baseUrl = base[:base.rindex("/")]
        for n in needles:
            if "://" not in n[URL_INDEX]:
                if not baseUrlLogged:
                    Logger.Debug("Using baseUrl %s for M3u8", baseUrl)
                    baseUrlLogged = True
                sub = "%s/%s" % (baseUrl, n[URL_INDEX])
            else:
                if not baseUrlLogged:
                    Logger.Debug("Full url found in M3u8")
                    baseUrlLogged = True
                sub = n[URL_INDEX]

            if qs is not None and sub.endswith("?null="):
                sub = sub.replace("?null=", "?%s" % (qs, ))
            elif qs is not None and "?" in sub:
                sub = "%s&%s" % (sub, qs)
            elif qs is not None:
                sub = "%s?%s" % (sub, qs)

        return sub

    @staticmethod
    def SetInputStreamAddonInput(strm, proxy=None, headers=None,
                                 licenseKey=None, licenseType=None):
        return Adaptive.SetInputStreamAddonInput(strm, proxy, headers, manifestType="hls",
                                                 licenseKey=licenseKey, licenseType=licenseType)

    @staticmethod
    def GetStreamsFromM3u8(url, proxy=None, headers=None, appendQueryString=False, mapAudio=False,
                           playListData=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening
        @param url:               (String) The url to download
        @param appendQueryString: (boolean) should the existing query string be appended?
        @param mapAudio:          (boolean) map audio streams
        @param playListData:      (string) data of an already retrieved M3u8

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        streams = []

        data = playListData or UriHandler.Open(url, proxy, additionalHeaders=headers)
        Logger.Trace(data)

        qs = None
        if appendQueryString and "?" in url:
            base, qs = url.split("?", 1)
            Logger.Info("Going to append QS: %s", qs)
        elif "?" in url:
            base, qs = url.split("?", 1)
            Logger.Info("Ignoring QS: %s", qs)
            qs = None
        else:
            base = url

        Logger.Debug("Processing M3U8 Streams: %s", url)

        # If we need audio
        if mapAudio:
            audioNeedle = '(#\w[^:]+):TYPE=AUDIO()[^\r\n]+ID="([^"]+)"[^\n\r]+URI="([^"]+.m3u8[^"]*)"'
            needles = Regexer.DoRegex(audioNeedle, data)
            needle = '(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}(?:[^\r\n]*AUDIO="([^"]+)"){0,1}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)'
            needles += Regexer.DoRegex(needle, data)
            TYPE_INDEX = 0
            BITRATE_INDEX = 1
            ID_INDEX = 2
            URL_INDEX = 3
        else:
            needle = "(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
            needles = Regexer.DoRegex(needle, data)
            TYPE_INDEX = 0
            BITRATE_INDEX = 1
            URL_INDEX = 2

        audioStreams = {}
        baseUrlLogged = False
        baseUrl = base[:base.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.Trace(n)

            if "#EXT-X-I-FRAME" in n[TYPE_INDEX]:
                continue

            if "://" not in n[URL_INDEX]:
                if not baseUrlLogged:
                    Logger.Debug("Using baseUrl %s for M3u8", baseUrl)
                    baseUrlLogged = True
                stream = "%s/%s" % (baseUrl, n[URL_INDEX])
            else:
                if not baseUrlLogged:
                    Logger.Debug("Full url found in M3u8")
                    baseUrlLogged = True
                stream = n[URL_INDEX]
            bitrate = n[BITRATE_INDEX]

            if qs is not None and stream.endswith("?null="):
                stream = stream.replace("?null=", "?%s" % (qs, ))
            elif qs is not None and "?" in stream:
                stream = "%s&%s" % (stream, qs)
            elif qs is not None:
                stream = "%s?%s" % (stream, qs)

            if mapAudio and "#EXT-X-MEDIA" in n[TYPE_INDEX]:
                Logger.Debug("Found audio stream: %s -> %s", n[ID_INDEX], stream)
                audioStreams[n[ID_INDEX]] = stream
                continue

            if mapAudio:
                streams.append((stream, bitrate, audioStreams.get(n[ID_INDEX]) or None))
            else:
                streams.append((stream, bitrate))

        Logger.Debug("Found %s substreams in M3U8", len(streams))
        return streams


if __name__ == "__main__":
    from debug.initdebug import DebugInitializer
    DebugInitializer()

    # url = "http://tv4play-i.akamaihd.net/i/mp4root/2014-01-27/Bingolotto2601_2534830_,T6MP43,T6MP48,T6MP415,_.mp4.csmil/master.m3u8"
    # url = "http://iphone.streampower.be/een_nogeo/_definst_/2013/08/1000_130830_placetobe_marjolein_Website_Een_M4V.m4v/playlist.m3u8"
    # url = "http://livestreams.omroep.nl/live/npo/regionaal/rtvnoord2/rtvnoord2.isml/rtvnoord2.m3u8?protection=url"  # appendQueryString
    # url = "https://smoote1a.omroep.nl/urishieldv2/l2cm221c27e6ca0058c1adda000000.e6592cb04974c5ff/live/npo/tvlive/npo3/npo3.isml/npo3.m3u8"
    # url = "http://embed.kijk.nl/api/playlist/9JKFARNrJEz_dbzyr6.m3u8?user_token=S0nHgrI3Sh16XSxOpLm7m2Xt7&app_token=CgZzYW5vbWESEjlKS0ZBUk5ySkV6X2RienlyNhoOMTkzLjExMC4yMzQuMjIiGVMwbkhnckkzU2gxNlhTeE9wTG03bTJYdDcotIDZpKsrMgJoADoERlZPREIDU0JTShI5SktGQVJOckpFel9kYnp5cjY%3D%7CmGGy/TM5eOmoSCNwG2I4bGKvMBOvBD9YsadprKSVqv4%3D&base_url=http%3A//emp-prod-acc-we.ebsd.ericsson.net/sbsgroup"
    # url = "http://manifest.us.rtl.nl/rtlxl/v166/network/pc/adaptive/components/soaps/theboldandthebeautiful/338644/4c1b51b9-864d-31fe-ba53-7ea6da0b614a.ssm/4c1b51b9-864d-31fe-ba53-7ea6da0b614a.m3u8"
    url = "http://svtplay2r-f.akamaihd.net/i/world/open/20170307/1377039-008A/PG-1377039-008A-AGENDA2017-03_,988,240,348,456,636,1680,2796,.mp4.csmil/master.m3u8"
    url = "http://livestreams.omroep.nl/live/npo/regionaal/rtvnoord2/rtvnoord2.isml/rtvnoord2.m3u8?protection=url"
    url = "https://ondemand-w.lwc.vrtcdn.be/content/vod/vid-dd0ddbe5-7a83-477a-80d0-6e9c75369c1e-CDN_2/vid-dd0ddbe5-7a83-477a-80d0-6e9c75369c1e-CDN_2_nodrm_a635917e-abe5-49d4-a202-e81b6cfa08a0.ism/.m3u8?test=1"  # audio streams
    results = M3u8.GetStreamsFromM3u8(url, DebugInitializer.Proxy, appendQueryString=True, mapAudio=True)
    results.sort(lambda x, y: cmp(int(x[1]), int(y[1])))
    a = None
    for s, b, a in results:
        if s.count("://") > 1:
            raise Exception("Duplicate protocol in url: %s", s)
        print "%s - %s (%s)" % (b, s, a)
        Logger.Info("%s - %s (%s)", b, s, a)

    Logger.Instance().CloseLog()
