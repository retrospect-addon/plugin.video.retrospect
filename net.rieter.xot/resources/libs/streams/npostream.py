#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import os
import time

from helpers.jsonhelper import JsonHelper
from streams.m3u8 import M3u8
from urihandler import UriHandler
from logger import Logger
from regexer import Regexer


class NpoStream:
    def __init__(self):
        pass

    @staticmethod
    def GetLiveStreamsFromNpo(url, cacheDir, proxy=None, headers=None):
        """ Retrieve NPO Player Live streams from a different number of stream urls.

        @param url:               (String) The url to download
        @param cacheDir:          (String) The cache dir where to find the 'uzg-i.js' file.
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in NpoStream.GetStreamsFromNpo(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        if url.startswith("http://ida.omroep.nl/aapi/"):
            Logger.Debug("Already found an IDA data url '%s'. Using it to fetch the streams.", url)
            # we already have the m3u8
            actualStreamData = UriHandler.Open(
                url,
                proxy=proxy,
                additionalHeaders=headers)

            url = NpoStream.__FetchActualStream(actualStreamData, proxy)

        elif url.endswith("m3u8"):
            Logger.Debug("Found a stream url '%s'. Using a call to IDA to determine the actual streams.", url)
            hashCode = NpoStream.GetNpoToken(proxy, cacheDir)
            actualStreamData = UriHandler.Open(
                "http://ida.omroep.nl/aapi/?stream=%s&token=%s" % (url, hashCode),
                proxy=proxy,
                additionalHeaders=headers)
            url = NpoStream.__FetchActualStream(actualStreamData, proxy)

        elif url.startswith("http://e.omroep.nl/metadata/"):
            Logger.Debug("Found a metadata url '%s'. Determining the actual stream url's", url)
            jsonData = UriHandler.Open(url, proxy=proxy)
            json = JsonHelper(jsonData, Logger.Instance())
            streams = []
            for stream in json.GetValue("streams"):
                if stream['type'] != "hls":
                    continue
                url = stream['url']
                for k, v in NpoStream.GetLiveStreamsFromNpo(url, cacheDir, proxy=proxy, headers=headers):
                    streams.append((k, v))
            return streams
        else:
            Logger.Warning("None-stream url found: %s", url)
            return []

        return M3u8.GetStreamsFromM3u8(url, proxy=proxy)

    @staticmethod
    def GetNpoToken(proxy, cacheDir):
        tokenUrl = "http://ida.omroep.nl/npoplayer/i.js"
        tokenExpired = True
        tokenFile = "uzg-i.js"
        tokenPath = os.path.join(cacheDir, tokenFile)

        # determine valid token
        if os.path.exists(tokenPath):
            mTime = os.path.getmtime(tokenPath)
            timeDiff = time.time() - mTime
            maxTime = 30 * 60  # if older than 15 minutes, 30 also seems to work.
            Logger.Debug("Found token '%s' which is %s seconds old (maxAge=%ss)", tokenFile,
                         timeDiff, maxTime)
            if timeDiff > maxTime:
                Logger.Debug("Token expired.")
                tokenExpired = True
            elif timeDiff < 0:
                Logger.Debug("Token modified time is in the future. Ignoring token.")
                tokenExpired = True
            else:
                tokenExpired = False
        else:
            Logger.Debug("No Token Found.")

        if tokenExpired:
            Logger.Debug("Fetching a Token.")
            tokenData = UriHandler.Open(tokenUrl, proxy=proxy, noCache=True)
            tokenHandle = file(tokenPath, 'w')
            tokenHandle.write(tokenData)
            tokenHandle.close()
            Logger.Debug("Token saved for future use.")
        else:
            Logger.Debug("Reusing an existing Token.")
            # noinspection PyArgumentEqualDefault
            tokenHandle = file(tokenPath, 'r')
            tokenData = tokenHandle.read()
            tokenHandle.close()

        token = Regexer.DoRegex('npoplayer.token = "([^"]+)', tokenData)[-1]
        actualToken = NpoStream.__SwapToken(token)
        Logger.Info("Found NOS token: %s\n          was: %s\n", actualToken, token)
        return actualToken

    @staticmethod
    def __FetchActualStream(idaData, proxy):
        actualStreamJson = JsonHelper(idaData, Logger.Instance())
        m3u8Url = actualStreamJson.GetValue('stream')
        Logger.Debug("Fetching redirected stream for: %s", m3u8Url)

        # now we have the m3u8 URL, but it will do a HTML 302 redirect
        (headData, m3u8Url) = UriHandler.Header(m3u8Url, proxy=proxy)  # : @UnusedVariables

        Logger.Debug("Found redirected stream: %s", m3u8Url)
        return m3u8Url

    @staticmethod
    def __SwapToken(token):
        """ Swaps some chars of the token to make it a valid one. NPO introduced this in july 2015

        @param token: the original token from their file.

        @return: the swapped version

        """

        first = -1
        second = -1
        startAt = 5
        Logger.Debug("Starting Token swap at position in: %s %s %s", token[0:startAt],
                     token[startAt:len(token) - startAt], token[len(token) - startAt:])
        for i in range(startAt, len(token) - startAt, 1):
            # Logger.Trace("Checking %s", token[i])
            if token[i].isdigit():
                if first < 0:
                    first = i
                    Logger.Trace("Storing first digit at position %s: %s", first, token[i])
                elif second < 0:
                    second = i
                    Logger.Trace("Storing second digit at position %s: %s", second, token[i])
                    break

        # swap them
        newToken = list(token)
        if first < 0 or second < 0:
            Logger.Debug("No number combo found in range %s. Swapping middle items",
                         token[startAt:len(token) - startAt])
            first = 12
            second = 13

        Logger.Debug("Swapping position %s with %s", first, second)
        newToken[first] = token[second]
        newToken[second] = token[first]
        newToken = ''.join(newToken)
        return newToken

if __name__ == "__main__":
    from debug.initdebug import DebugInitializer
    DebugInitializer()
    cacheDir = os.path.join("..", "..", "..", "..", "..", "net.rieter.xot.userdata", "cache")

    # url = "http://livestreams.omroep.nl/live/regionaal/l1/l1tv/l1tv.isml/l1tv.m3u8"
    url = "http://e.omroep.nl/metadata/LI_NEDERLAND3_136696"
    # token = NpoStream.GetNpoToken(DebugInitializer.Proxy, cacheDir)
    # url = "http://ida.omroep.nl/aapi/?stream=http://livestreams.omroep.nl/live/npo/tvlive/ned3/ned3.isml/ned3.m3u8&token=%s" % (token, )

    results = NpoStream.GetLiveStreamsFromNpo(url, cacheDir, proxy=DebugInitializer.Proxy)
    results.sort(lambda x, y: cmp(int(x[1]), int(y[1])))
    for s, b in results:
        if s.count("://") > 1:
            raise Exception("Duplicate protocol in url: %s", s)
        print "%s - %s" % (b, s)
        Logger.Info("%s - %s", b, s)

    # some test cases
    tokenTests = {
        "kouansr1o89hu1u0lnr20b6f60": "kouansr8o19hu1u0lnr20b6f60",
        "h05npjekmn478nhfqft7g2i6q1": "h05npjekmn748nhfqft7g2i6q1",
        "ncjamt9gu2d9qmg4dpu1plqd37": "ncjamt2gu9d9qmg4dpu1plqd37",
        "m9mvj51ittnuglub3ibgoptvi4": "m9mvj15ittnuglub3ibgoptvi4",
        "vgkn9j8r3135a7vf0e6992vmi1": "vgkn9j3r8135a7vf0e6992vmi1",
        "eqn86lpcdadda9ajrceedcpef3": "eqn86lpcdadd9aajrceedcpef3",
        "vagiq9ejnqbmcodtncp77uomj1": "vagiq7ejnqbmcodtncp97uomj1",
    }

    for inputToken, outputToken in tokenTests.iteritems():
        # noinspection PyUnresolvedReferences,PyProtectedMember
        token = NpoStream._NpoStream__SwapToken(inputToken)
        if token != outputToken:
            raise Exception("Token mismatch:\nInput:   %s\nOutput:  %s\nShould be: %s")

    Logger.Instance().CloseLog()
