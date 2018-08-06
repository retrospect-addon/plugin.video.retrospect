#==============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import xbmc

from logger import Logger
from helpers.htmlentityhelper import HtmlEntityHelper
from regexer import Regexer
from urihandler import UriHandler


class YouTube:
    def __init__(self):
        """ Creates a Youtube Parsing class """
        pass

# http://en.wikipedia.org/wiki/YouTube#Quality_and_codecs
    __YouTubeEncodings = {
        # Flash Video
        5: [314, "flv", "240p", "Sorenson H.263", "N/A", "0.25", "MP3", "64"],
        6: [864, "flv", "270p", "Sorenson H.263", "N/A", "0.8", "MP3", "64"],
        34: [628, "flv", "360p", "H.264", "Main", "0.5", "AAC", "128"],
        35: [1028, "flv", "480p", "H.264", "Main", "0.8-1", "AAC", "128"],

        # 3GP
        36: [208, "3gp", "240p", "MPEG-4 Visual", "Simple", "0.17", "AAC", "38"],
        13: [500, "3gp", "N/A", "MPEG-4 Visual", "N/A", "0.5", "AAC", "N/A"],
        17: [74, "3gp", "144p", "MPEG-4 Visual", "Simple", "0.05", "AAC", "24"],

        # MPEG-4
        18: [596, "mp4", "360p", "H.264", "Baseline", "0.5", "AAC", "96"],
        22: [2792, "mp4", "720p", "H.264", "High", "2-2.9", "AAC", "192"],
        37: [3800, "mp4", "1080p", "H.264", "High", "3-4.3", "AAC", "192"],
        38: [4500, "mp4", "3072p", "H.264", "High", "3.5-5", "AAC", "192"],
        82: [596, "mp4", "360p", "H.264", "3D", "0.5", "AAC", "96"],
        83: [596, "mp4", "240p", "H.264", "3D", "0.5", "AAC", "96"],
        84: [2752, "mp4", "720p", "H.264", "3D", "2-2.9", "AAC", "152"],
        85: [2752, "mp4", "520p", "H.264", "3D", "2-2.9", "AAC", "152"],

        # WebM
        43: [628, "webm", "360p", "VP8", "N/A", "0.5", "Vorbis", "128"],
        44: [1128, "webm", "480p", "VP8", "N/A", "1", "Vorbis", "128"],
        45: [2192, "webm", "720p", "VP8", "N/A", "2", "Vorbis", "192"],
        # 46: ["webm", "1080p", "VP8", "N/A", "N/A", "Vorbis", "192"],
        # 100: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "128"],
        # 101: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "192"],
        # 102: ["webm", "720p", "VP8", "3D", "N/A", "Vorbis", "192"]
    }

    @staticmethod
    def GetStreamsFromYouTube(url, proxy=None):
        """ Parsers standard YouTube videos and returns a list of tuples with streams and bitrates that can be used by
        other methods

        @param proxy:   Proxy  - The proxy to use for opening
        @param url:     String - The url to download

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in YouTube.GetStreamsFromYouTube(url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)
        """

        youTubeStreams = []
        youTubeAddOnAvailable = xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")') == 1

        if youTubeAddOnAvailable:
            Logger.Info("Found Youtube add-on. Using it")
            youTubeStreams.append((YouTube.__PlayYouTubeUrl(url), 0))
            Logger.Trace(youTubeStreams)
            return youTubeStreams

        Logger.Info("No Kodi Youtube Video add-on was found. Falling back.")

        if "watch?v=" in url:
            videoId = url.split("?v=")[-1]
            Logger.Debug("Using Youtube ID '%s' retrieved from '%s'", videoId, url)
            # get the meta data url
            url = "http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=%s" % (videoId, )

        elif "get_video_info" not in url:
            Logger.Error("Invalid Youtube URL specified: '%s'", url)
            return []

        data = UriHandler.Open(url, proxy=proxy)
        # get the stream data from the page

        # Up to 720p with audio and video combined.
        urlEncodedFmtStreamMap = Regexer.DoRegex("url_encoded_fmt_stream_map=([^&]+)", data)
        # Up to 4K with audio and video split.
        # urlEncodedFmtStreamMap = Regexer.DoRegex("adaptive_fmts=([^&]+)", data)
        urlEncodedFmtStreamMapData = HtmlEntityHelper.UrlDecode(urlEncodedFmtStreamMap[0])
        # split per stream
        streams = urlEncodedFmtStreamMapData.split(',')

        for stream in streams:
            # let's create a new part
            qsData = dict([x.split("=") for x in stream.split("&")])
            Logger.Trace(qsData)

            if "itag" in qsData and "bitrate" not in qsData:
                iTag = int(qsData.get('itag', -1))
                streamEncoding = YouTube.__YouTubeEncodings.get(iTag, None)
                if streamEncoding is None:
                    # if the iTag was not in the list, skip it.
                    Logger.Debug(
                        "Not using iTag %s as it is not in the list of supported encodings.", iTag)
                    continue
                bitrate = streamEncoding[0]
            else:
                bitrate = int(qsData['bitrate'])/1000

            signature = qsData.get('s', None)
            quality = qsData.get('quality_label', qsData.get('quality'))
            if not quality:
                Logger.Debug("Missing 'quality_label', skipping: %s", qsData)
                continue

            videoUrl = HtmlEntityHelper.UrlDecode(qsData['url'])
            if signature is None:
                url = videoUrl
            else:
                url = "%s&signature=%s" % (videoUrl, signature)

            youTubeStreams.append((url, bitrate))

        return youTubeStreams

    @staticmethod
    def __PlayYouTubeUrl(url):
        """ Plays a YouTube URL with the YouTube addon from XBMC.

        url = YouTube.PlayYouTubeUrl(url[0])
        part.AppendMediaStream(url, bitrate=0)

        @param url: The URL to playback in the format: http://www.youtube.com/watch?v=878-LYQEcPs
        @return: The plugin:// url for the YouTube addon
        """

        if "youtube" in url:
            Logger.Debug("Determining Add-on URL for YouTube: %s", url)
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=%s" % (url.split("v=")[1], )
        return url


if __name__ == "__main__":
    from debug.initdebug import DebugInitializer
    DebugInitializer()
    url = "http://www.youtube.com/watch?v=878-LYQEcPs"
    results = YouTube.GetStreamsFromYouTube(url, DebugInitializer.Proxy)
    results.sort(lambda x, y: cmp(int(x[1]), int(y[1])))
    for s, b in results:
        if s.count("://") > 1:
            raise Exception("Duplicate protocol in url: %s", s)
        print "%s - %s" % (b, s)
        Logger.Info("%s - %s", b, s)

    Logger.Instance().CloseLog()
