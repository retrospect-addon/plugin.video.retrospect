#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from helpers.jsonhelper import JsonHelper
from streams.m3u8 import M3u8
from streams.mpd import Mpd
from helpers.subtitlehelper import SubtitleHelper
from urihandler import UriHandler
from logger import Logger


class NpoStream:
    def __init__(self):
        pass

    @staticmethod
    def GetSubtitle(streamId, proxy=None):
        subTitleUrl = "http://tt888.omroep.nl/tt888/%s" % (streamId,)
        return SubtitleHelper.DownloadSubtitle(subTitleUrl, streamId + ".srt", format='srt', proxy=proxy)

    @staticmethod
    def AddMpdStreamFromNpo(url, episodeId, part, proxy=None, headers=None):
        """ Extracts the Dash streams for the given url or episode id

        @param url:               (String) The url to download
        @param episodeId:         (String) The NPO episode ID
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening

        for s, b, p in NpoStream.GetMpdStreamFromNpo(None, episodeId, proxy=self.proxy):
            item.complete = True
            stream = part.AppendMediaStream(s, b)
            for k, v in p.iteritems():
                stream.AddProperty(k, v)

        """

        if url:
            Logger.Info("Determining MPD streams for url: %s", url)
            episodeId = url.split("/")[-1]
        elif episodeId:
            Logger.Info("Determining MPD streams for VideoId: %s", episodeId)
        else:
            Logger.Error("No url or streamId specified!")
            return

        # https://www.npo.nl/player/KN_1693703 -> token
        data = UriHandler.Open("https://www.npostart.nl/player/{0}".format(episodeId),
                               params="autoplay=1",
                               proxy=proxy,
                               additionalHeaders=headers)
        token = JsonHelper(data).GetValue("token")
        Logger.Trace("Found token %s", token)

        streamDataUrl = "https://start-player.npo.nl/video/{0}/streams?" \
                        "profile=dash-widevine" \
                        "&quality=npo" \
                        "&tokenId={1}" \
                        "&streamType=broadcast" \
                        "&mobile=0" \
                        "&isChromecast=0".format(episodeId, token)

        data = UriHandler.Open(streamDataUrl, proxy=proxy, additionalHeaders=headers)
        streamData = JsonHelper(data)
        licenseUrl = streamData.GetValue("stream", "keySystemOptions", 0, "options", "licenseUrl")
        licenseHeaders = streamData.GetValue("stream", "keySystemOptions", 0, "options", "httpRequestHeaders")
        if licenseHeaders:
            licenseHeaders = '&'.join(["{}={}".format(k, v) for k, v in licenseHeaders.items()])

        streamUrl = streamData.GetValue("stream", "src")
        licenseType = streamData.GetValue("stream", "keySystemOptions", 0, "name")
        licenseKey = "{0}|{1}|R{{SSM}}|".format(licenseUrl, licenseHeaders or "")

        # Actually set the stream
        stream = part.AppendMediaStream(streamUrl, 0)
        M3u8.SetInputStreamAddonInput(stream, proxy, headers)
        Mpd.SetInputStreamAddonInput(stream, proxy, headers,
                                     licenseKey=licenseKey,
                                     licenseType=licenseType)
        return

    @staticmethod
    def GetStreamsFromNpo(url, episodeId, proxy=None, headers=None):
        """ Retrieve NPO Player Live streams from a different number of stream urls.

        @param url:               (String) The url to download
        @param episodeId:         (String) The NPO episode ID
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in NpoStream.GetStreamsFromNpo(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        if url:
            Logger.Info("Determining streams for url: %s", url)
            episodeId = url.split("/")[-1]
        elif episodeId:
            Logger.Info("Determining streams for VideoId: %s", episodeId)
        else:
            Logger.Error("No url or streamId specified!")
            return []

        # we need an hash code
        tokenJsonData = UriHandler.Open("http://ida.omroep.nl/app.php/auth",
                                        noCache=True, proxy=proxy, additionalHeaders=headers)
        tokenJson = JsonHelper(tokenJsonData)
        token = tokenJson.GetValue("token")

        url = "http://ida.omroep.nl/app.php/%s?adaptive=yes&token=%s" % (episodeId, token)
        streamData = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
        if not streamData:
            return []

        streamJson = JsonHelper(streamData, logger=Logger.Instance())
        streamInfos = streamJson.GetValue("items")[0]
        Logger.Trace(streamInfos)
        streams = []
        for streamInfo in streamInfos:
            Logger.Debug("Found stream info: %s", streamInfo)
            if streamInfo["format"] == "mp3":
                streams.append((streamInfo["url"], 0))
                continue

            elif streamInfo["contentType"] == "live":
                Logger.Debug("Found live stream")
                url = streamInfo["url"]
                url = url.replace("jsonp", "json")
                liveUrlData = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
                liveUrl = liveUrlData.strip("\"").replace("\\", "")
                Logger.Trace(liveUrl)
                streams += M3u8.GetStreamsFromM3u8(liveUrl, proxy, headers=headers)

            elif streamInfo["format"] == "hls":
                m3u8InfoUrl = streamInfo["url"]
                m3u8InfoData = UriHandler.Open(m3u8InfoUrl, proxy=proxy, additionalHeaders=headers)
                m3u8InfoJson = JsonHelper(m3u8InfoData, logger=Logger.Instance())
                m3u8Url = m3u8InfoJson.GetValue("url")
                streams += M3u8.GetStreamsFromM3u8(m3u8Url, proxy, headers=headers)

            elif streamInfo["format"] == "mp4":
                bitrates = {"hoog": 1000, "normaal": 500}
                url = streamInfo["url"]
                if "contentType" in streamInfo and streamInfo["contentType"] == "url":
                    mp4Url = url
                else:
                    url = url.replace("jsonp", "json")
                    mp4UrlData = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
                    mp4InfoJson = JsonHelper(mp4UrlData, logger=Logger.Instance())
                    mp4Url = mp4InfoJson.GetValue("url")
                bitrate = bitrates.get(streamInfo["label"].lower(), 0)
                if bitrate == 0 and "/ipod/" in mp4Url:
                    bitrate = 200
                elif bitrate == 0 and "/mp4/" in mp4Url:
                    bitrate = 500
                streams.append((mp4Url, bitrate))

        return streams
