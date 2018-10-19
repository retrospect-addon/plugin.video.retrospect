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
    def get_subtitle(stream_id, proxy=None):
        sub_title_url = "http://tt888.omroep.nl/tt888/%s" % (stream_id,)
        return SubtitleHelper.download_subtitle(sub_title_url, stream_id + ".srt", format='srt', proxy=proxy)

    @staticmethod
    def add_mpd_stream_from_npo(url, episode_id, part, proxy=None, headers=None):
        """ Extracts the Dash streams for the given url or episode id

        @param url:               (String) The url to download
        @param episode_id:         (String) The NPO episode ID
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
            episode_id = url.split("/")[-1]
        elif episode_id:
            Logger.Info("Determining MPD streams for VideoId: %s", episode_id)
        else:
            Logger.Error("No url or streamId specified!")
            return

        # https://www.npo.nl/player/KN_1693703 -> token
        data = UriHandler.Open("https://www.npostart.nl/player/{0}".format(episode_id),
                               params="autoplay=1",
                               proxy=proxy,
                               additionalHeaders=headers)
        token = JsonHelper(data).get_value("token")
        Logger.Trace("Found token %s", token)

        stream_data_url = "https://start-player.npo.nl/video/{0}/streams?" \
                          "profile=dash-widevine" \
                          "&quality=npo" \
                          "&tokenId={1}" \
                          "&streamType=broadcast" \
                          "&mobile=0" \
                          "&isChromecast=0".format(episode_id, token)

        data = UriHandler.Open(stream_data_url, proxy=proxy, additionalHeaders=headers)
        stream_data = JsonHelper(data)
        license_url = stream_data.get_value("stream", "keySystemOptions", 0, "options", "licenseUrl")
        license_headers = stream_data.get_value("stream", "keySystemOptions", 0, "options", "httpRequestHeaders")
        if license_headers:
            license_headers = '&'.join(["{}={}".format(k, v) for k, v in license_headers.items()])

        stream_url = stream_data.get_value("stream", "src")
        license_type = stream_data.get_value("stream", "keySystemOptions", 0, "name")
        license_key = "{0}|{1}|R{{SSM}}|".format(license_url, license_headers or "")

        # Actually set the stream
        stream = part.AppendMediaStream(stream_url, 0)
        M3u8.set_input_stream_addon_input(stream, proxy, headers)
        Mpd.set_input_stream_addon_input(stream, proxy, headers,
                                         license_key=license_key,
                                         license_type=license_type)
        return

    @staticmethod
    def get_streams_from_npo(url, episode_id, proxy=None, headers=None):
        """ Retrieve NPO Player Live streams from a different number of stream urls.

        @param url:               (String) The url to download
        @param episode_id:         (String) The NPO episode ID
        @param headers:           (dict) Possible HTTP Headers
        @param proxy:             (Proxy) The proxy to use for opening

        Can be used like this:

            part = item.CreateNewEmptyMediaPart()
            for s, b in NpoStream.get_streams_from_npo(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        """

        if url:
            Logger.Info("Determining streams for url: %s", url)
            episode_id = url.split("/")[-1]
        elif episode_id:
            Logger.Info("Determining streams for VideoId: %s", episode_id)
        else:
            Logger.Error("No url or streamId specified!")
            return []

        # we need an hash code
        token_json_data = UriHandler.Open("http://ida.omroep.nl/app.php/auth",
                                          noCache=True, proxy=proxy, additionalHeaders=headers)
        token_json = JsonHelper(token_json_data)
        token = token_json.get_value("token")

        url = "http://ida.omroep.nl/app.php/%s?adaptive=yes&token=%s" % (episode_id, token)
        stream_data = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
        if not stream_data:
            return []

        stream_json = JsonHelper(stream_data, logger=Logger.Instance())
        stream_infos = stream_json.get_value("items")[0]
        Logger.Trace(stream_infos)
        streams = []
        for streamInfo in stream_infos:
            Logger.Debug("Found stream info: %s", streamInfo)
            if streamInfo["format"] == "mp3":
                streams.append((streamInfo["url"], 0))
                continue

            elif streamInfo["contentType"] == "live":
                Logger.Debug("Found live stream")
                url = streamInfo["url"]
                url = url.replace("jsonp", "json")
                live_url_data = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
                live_url = live_url_data.strip("\"").replace("\\", "")
                Logger.Trace(live_url)
                streams += M3u8.get_streams_from_m3u8(live_url, proxy, headers=headers)

            elif streamInfo["format"] == "hls":
                m3u8_info_url = streamInfo["url"]
                m3u8_info_data = UriHandler.Open(m3u8_info_url, proxy=proxy, additionalHeaders=headers)
                m3u8_info_json = JsonHelper(m3u8_info_data, logger=Logger.Instance())
                m3u8_url = m3u8_info_json.get_value("url")
                streams += M3u8.get_streams_from_m3u8(m3u8_url, proxy, headers=headers)

            elif streamInfo["format"] == "mp4":
                bitrates = {"hoog": 1000, "normaal": 500}
                url = streamInfo["url"]
                if "contentType" in streamInfo and streamInfo["contentType"] == "url":
                    mp4_url = url
                else:
                    url = url.replace("jsonp", "json")
                    mp4_url_data = UriHandler.Open(url, proxy=proxy, additionalHeaders=headers)
                    mp4_info_json = JsonHelper(mp4_url_data, logger=Logger.Instance())
                    mp4_url = mp4_info_json.get_value("url")
                bitrate = bitrates.get(streamInfo["label"].lower(), 0)
                if bitrate == 0 and "/ipod/" in mp4_url:
                    bitrate = 200
                elif bitrate == 0 and "/mp4/" in mp4_url:
                    bitrate = 500
                streams.append((mp4_url, bitrate))

        return streams
