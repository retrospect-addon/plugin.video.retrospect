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
from helpers.subtitlehelper import SubtitleHelper
from streams.mms import Mms
from urihandler import UriHandler
from logger import Logger
from regexer import Regexer
from proxyinfo import ProxyInfo


class NpoStream:
    def __init__(self):
        pass

    @staticmethod
    def GetSubtitle(streamId, proxy=None):
        subTitleUrl = "http://tt888.omroep.nl/tt888/%s" % (streamId,)
        return SubtitleHelper.DownloadSubtitle(subTitleUrl, streamId + ".srt", format='srt', proxy=proxy)

    @staticmethod
    def GetStreamsFromNpo(url, episodeId, cacheDir=None, proxy=None, headers=None):
        """ Retrieve NPO Player Live streams from a different number of stream urls.

                @param url:               (String) The url to download
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
