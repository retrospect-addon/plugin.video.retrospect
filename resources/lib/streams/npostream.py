# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.streams.inputstream import InputStreamAdaptiveDrmConfig
from typing import Optional

from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.inputstream import InputStream
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem


class NpoStream(object):
    def __init__(self):
        pass

    @staticmethod
    def get_subtitle(stream_id):
        """ Downloads a subtitle for a POMS id.

        :param str stream_id:   The POMS id.

        :return: The full patch of the cached SRT file.
        :rtype: str

        """

        sub_title_url = "http://tt888.omroep.nl/tt888/%s" % (stream_id,)
        return SubtitleHelper.download_subtitle(sub_title_url, stream_id + ".srt", format='srt')

    @staticmethod
    def add_mpd_stream_from_npo(url, episode_id: str, item: MediaItem,
                                headers: Optional[dict] = None, live: bool = False,
                                use_post: bool = False) -> Optional[str]:
        """ Extracts the Dash streams for the given url or episode id

        :param str|None url:        The url to download
        :param str episode_id:      The NPO episode ID
        :param MediaItem item:      The Media item to update
        :param dict headers:        Possible HTTP Headers
        :param bool live:           Is this a live stream?
        :param bool use_post:       Use a POST request.

        :rtype: str|None
        :return: An error message if an error occurred.

        for s, b, p in NpoStream.GetMpdStreamFromNpo(None, episodeId):
            item.complete = True
            stream = part.append_media_stream(s, b)
            for k, v in p.iteritems():
                stream.add_property(k, v)

        """

        if url:
            Logger.info("NPO-Stream: Determining MPD streams for url: %s", url)
            episode_id = url.split("/")[-1]
        elif episode_id:
            Logger.info("NPO-Stream: Determining MPD streams for VideoId: %s", episode_id)
        else:
            Logger.error("NPO-Stream: No url or streamId specified!")
            return None

        if use_post:
            token_data = {"productId": episode_id}
            token = UriHandler.open(
                "https://npo.nl/start/api/domain/player-token", json=token_data, no_cache=True)
        else:
            token = UriHandler.open(
                f"https://npo.nl/start/api/domain/player-token?productId={episode_id}", no_cache=True)

        token_json = JsonHelper(token)
        token_value = token_json.get_value("jwt")

        video_headers = {"authorization": token_value}
        video_data = {
            "profileName": "dash",
            "drmType": "widevine",
            "referrerUrl": "https://npo.nl/"
        }
        data = UriHandler.open(
            "https://prod.npoplayer.nl/stream-link", json=video_data, additional_headers=video_headers, no_cache=True)
        video_info = JsonHelper(data)

        status = video_info.get_value("status", fallback=0)
        if status:
            message = video_info.get_value("body")
            return message

        stream_url = video_info.get_value("stream", "streamURL")
        drm_info = video_info.get_value("stream", "drm", fallback=None)
        drm_token = None
        drm_license_url: str = ""
        drm_certificate: Optional[str] = None
        drm_headers = {}
        drm_config: Optional[InputStreamAdaptiveDrmConfig] = None

        if drm_info:
            drm_token = drm_info.get("drmToken", None)
            drm_license_url = drm_info.get("licenseUrl", None)
            drm_certificate = drm_info.get("certificateUrl", None)
            drm_headers = drm_info.get("httpHeaders", {})

        input_stream = InputStream()

        # Encryption?
        if drm_token:
            Logger.info(f"NPO-Stream: Using encrypted Dash with Token for NPO")
            drm_license_url = f"https://npo-drm-gateway.samgcloud.nepworldwide.nl/authentication?custom_data={drm_token}"
            Logger.info("NPO-Stream: Using encrypted Dash for NPO")
            drm_config = InputStreamAdaptiveDrmConfig(
                license_type="com.widevine.alpha",
                server_url=drm_license_url
            )

        elif drm_license_url:
            Logger.info(f"NPO-Stream: Using encrypted Dash with License Key for NPO: {drm_license_url}")
            key_headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
                "origin": "https://npo.nl",
                "referer": "https://npo.nl/",
            }
            if drm_headers:
                Logger.info(f"NPO-Stream: Adding custom headers: {','.join(drm_headers.keys())}")
                key_headers.update(drm_headers)

            if drm_certificate:
                Logger.info(f"NPO-Stream: Received DRM Server Certificate {drm_certificate}.")
                cert_data = UriHandler.open(drm_certificate)
                drm_certificate = EncodingHelper.encode_base64(cert_data).decode('ascii')

            # Create a DRM configuration
            drm_config = InputStreamAdaptiveDrmConfig(
                license_type="com.widevine.alpha",
                server_url=drm_license_url,
                server_certificate=drm_certificate,
                headers=key_headers
            )
        else:
            Logger.info("NPO-Stream: Using non-encrypted Dash for NPO")

        # Actually set the stream
        stream = item.add_stream(stream_url, 0)
        input_stream.set_input_stream_addon_input(
            stream,
            drm_config=drm_config,
            stream_headers=headers,
        )
        return None
