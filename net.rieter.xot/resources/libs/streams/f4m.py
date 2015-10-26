from urihandler import UriHandler
from logger import Logger
from regexer import Regexer


class F4m:
    def __init__(self):
        pass

    @staticmethod
    def GetStreamsFromF4m(url, proxy=None, headers=None):
        """ Parsers standard F4m lists and returns a list of tuples with streams and bitrates that can be used by
        other methods

        @type headers: dict   - Possible HTTP Headers
        @param proxy:  Proxy  - The proxy to use for opening
        @param url:    String - The url to download

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in F4m.GetStreamsFromF4m(url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        streams = []

        data = UriHandler.Open(url, proxy, additionalHeaders=headers)
        Logger.Trace(data)
        Logger.Debug("Processing F4M Streams: %s", url)
        needle = '<media href="([^"]+)"[^>]*bitrate="([^"]+)"'
        needles = Regexer.DoRegex(needle, data)

        baseUrlLogged = False
        baseUrl = url[:url.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.Trace(n)
            if "://" not in n[0]:
                if not baseUrlLogged:
                    Logger.Trace("Using baseUrl %s for F4M", baseUrl)
                    baseUrlLogged = True
                stream = "%s/%s" % (baseUrl, n[0])
            else:
                if not baseUrlLogged:
                    Logger.Trace("Full url found in F4M")
                    baseUrlLogged = True
                stream = n[0]
            bitrate = int(n[1])
            streams.append((stream, bitrate))

        Logger.Debug("Found %s substreams in F4M", len(streams))
        return streams
