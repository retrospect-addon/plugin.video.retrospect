# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Optional, Dict

from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer
from resources.lib.streams.adaptive import Adaptive
from resources.lib.mediaitem import MediaStream, MediaItem
from resources.lib.addonsettings import AddonSettings


class M3u8(object):
    def __init__(self):
        pass

    @staticmethod
    def get_subtitle(url, play_list_data=None, append_query_string=True, language=None):  # NOSONAR
        """ Retrieves a subtitle url either from a M3u8 file via HTTP or alternatively from a
        M3u8 playlist string value (in case it was already retrieved).

        :param str url:                     The M3u8 url that contains the subtitle information.
        :param str play_list_data:          The data (in case the URL was already retrieved).
        :param bool append_query_string:    Should we re-append the query string?
        :param str language:                The language to select (if multiple are present).

        :return: The subtitle url for the M3u8 file.
        :rtype: str

        """

        data = play_list_data or UriHandler.open(url)
        regex = r'(#\w[^:]+)[^\n]+TYPE=SUBTITLES[^\n]*LANGUAGE="(\w+)"[^\n]*\W+URI="([^"]+.m3u8[^"\n\r]*)'
        sub = ""

        qs = None
        if append_query_string and "?" in url:
            base, qs = url.split("?", 1)
            Logger.info("Going to append QS: %s", qs)
        elif "?" in url:
            base, qs = url.split("?", 1)
            Logger.info("Ignoring QS: %s", qs)
            qs = None
        else:
            base = url

        needles = Regexer.do_regex(regex, data)
        url_index = 2
        language_index = 1
        base_url_logged = False
        base_url = base[:base.rindex("/")]
        for n in needles:
            if language is not None and n[language_index] != language:
                Logger.debug("Found incorrect language: %s", n[language_index])
                continue

            if "://" not in n[url_index]:
                if not base_url_logged:
                    Logger.debug("Using base_url %s for M3u8", base_url)
                    base_url_logged = True
                sub = "%s/%s" % (base_url, n[url_index])
            else:
                if not base_url_logged:
                    Logger.debug("Full url found in M3u8")
                    base_url_logged = True
                sub = n[url_index]

            if qs is not None and sub.endswith("?null="):
                sub = sub.replace("?null=", "?%s" % (qs, ))
            elif qs is not None and "?" in sub:
                sub = "%s&%s" % (sub, qs)
            elif qs is not None:
                sub = "%s?%s" % (sub, qs)

        return sub

    @staticmethod
    def set_input_stream_addon_input(strm: MediaStream,
                                     stream_headers: Optional[Dict[str, str]] = None,
                                     stream_parameters: Optional[Dict[str, str]] = None,

                                     license_key: Optional[str] = None,
                                     license_type: Optional[str] = None,
                                     max_bit_rate: Optional[int] = 0,
                                     persist_storage: bool = False,
                                     service_certificate: Optional[str] = None,

                                     manifest_params: Optional[Dict[str, str]] = None,
                                     manifest_headers: Optional[Dict[str, str]] = None,
                                     manifest_update_params: Optional[str] = None,
                                     manifest_upd_params: Optional[Dict[str, str]] = None) -> MediaStream:

        """ Updates an existing stream with parameters for the inputstream adaptive add-on.

        :param strm:                    The MediaStream to update
        :param stream_headers:          Possible HTTP Headers for the stream.
        :param stream_parameters:       The stream parameters.
        :param license_key:             The value of the license key request
        :param license_type:            The type of license key request used (see below)
        :param max_bit_rate:            The maximum bitrate to use (optional)
        :param persist_storage:         Should we store certificates? And request server certificates?
        :param service_certificate:     Use the specified server certificate
        :param manifest_headers:        The headers to add to the manifest request.
        :param manifest_params:         The parameters to asdd to the manifest request.
        :param manifest_update_params:  How should the manifest be updated ("full"). Deprecated in v21
        :param manifest_upd_params:     The request parameters for the manifest update requests.

        Can be used like this:

            stream = item.add_stream(m3u8url, 0)
            M3u8.set_input_stream_addon_input(stream, self.headers)
            item.complete = True

        if maxBitRate is not set, the bitrate will be configured via the normal generic Retrospect
        or channel settings.

        """

        return Adaptive.set_input_stream_addon_input(strm,
                                                     stream_headers=stream_headers,
                                                     stream_parameters=stream_parameters,
                                                     manifest_type="hls",
                                                     license_key=license_key,
                                                     license_type=license_type,
                                                     max_bit_rate=max_bit_rate,
                                                     persist_storage=persist_storage,
                                                     service_certificate=service_certificate,
                                                     manifest_params=manifest_params,
                                                     manifest_headers=manifest_headers,
                                                     manifest_update_params=manifest_update_params,
                                                     manifest_upd_params=manifest_upd_params)

    @staticmethod
    def get_license_key(key_url, key_type="R", key_headers=None, key_value=None):
        """ Generates a propery license key value

        # A{SSM} -> not implemented
        # R{SSM} -> raw format
        # B{SSM} -> base64 format URL encoded (b{ssmm} will not URL encode)
        # D{SSM} -> decimal format

        The generic format for a LicenseKey is:
        |<url>|<headers>|<key with placeholders>|<optional json filter>

        The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

        :param str key_url:                 The URL where the license key can be obtained.
        :param str|None key_type:           The key type (A, R, B or D).
        :param dict[str,str] key_headers:   A dictionary that contains the HTTP headers to pass.
        :param str key_value:               The value that is beging passed on as the key value.

        :return: A formated license string that can be passed to the adaptive input add-on.
        :rtype: str

        """

        return Adaptive.get_license_key(key_url,
                                        key_type=key_type,
                                        key_headers=key_headers,
                                        key_value=key_value)

    @staticmethod
    def update_part_with_m3u8_streams(item, url,
                                      encrypted=False,
                                      headers=None,
                                      map_audio=False,
                                      bitrate=0,
                                      channel=None):
        """ Updates an existing MediaItem with M3u8 data either using the Adaptive Inputstream
        Add-on or with the built-in code.

        :param MediaItem item:          The MediaItem to update
        :param str url:                 The url to download
        :param bool encrypted:          Is the stream encrypted?
        :param dict[str,str] headers:   Possible HTTP Headers
        :param bool map_audio:          Should audio tracks be mapped separately?
        :param int bitrate:             Initial bitrate to use. Will be overridden later.
        :param ChannelInfo channel:     If specified, the channel specific configuration is
                                        considered.

        :return: indication if updating was successful.
        :rtype: bool

        """

        input_stream = AddonSettings.use_adaptive_stream_add_on(encrypted, channel=channel)
        if not input_stream and encrypted:
            Logger.error("Cannot play encrypted stream without InputStream Adaptive with Encryption support!")
            return False

        if input_stream:
            Logger.debug("Using InputStream Adaptive add-on for M3u8 playback.")
            stream = item.add_stream(url, bitrate)
            M3u8.set_input_stream_addon_input(stream, headers)
            return True

        complete = False
        if map_audio:
            Logger.debug("Using Retrospect code with Audio mapping for M3u8 playback.")
            for s, b, a in M3u8.get_streams_from_m3u8(url, map_audio=True):
                if a:
                    audio_part = a.rsplit("-", 1)[-1]
                    audio_part = "-%s" % (audio_part,)
                    s = s.replace(".m3u8", audio_part)
                item.add_stream(s, b)
                complete = True
        else:
            Logger.debug("Using Retrospect code for M3u8 playback.")
            for s, b in M3u8.get_streams_from_m3u8(url):
                item.add_stream(s, b)
                complete = True

        return complete

    @staticmethod
    def get_streams_from_m3u8(url,  # NOSONAR
                              headers=None,
                              append_query_string=False,
                              map_audio=False,
                              play_list_data=None):
        """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
        can be used by other methods.

        Can be used like this:

            for s, b in M3u8.get_streams_from_m3u8(m3u8_url):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                item.add_stream(s, b)

        :param dict[str,str] headers:       Possible HTTP Headers
        :param str url:                     The url to download
        :param bool append_query_string:    Should the existing query string be appended?
        :param bool map_audio:              Map audio streams
        :param str play_list_data:          Data of an already retrieved M3u8

        :return: a list of streams with their bitrate and optionally the audio streams.
        :rtype: list[tuple[str,str]|tuple[str,str,str]]

        """

        streams = []

        data = play_list_data or UriHandler.open(url, additional_headers=headers)
        Logger.trace(data)

        qs = None
        if append_query_string and "?" in url:
            base, qs = url.split("?", 1)
            Logger.info("Going to append QS: %s", qs)
        elif "?" in url:
            base, qs = url.split("?", 1)
            Logger.info("Ignoring QS: %s", qs)
            qs = None
        else:
            base = url

        Logger.debug("Processing M3U8 Streams: %s", url)

        # If we need audio
        if map_audio:
            audio_needle = r'(#\w[^:]+):TYPE=AUDIO()[^\r\n]+ID="([^"]+)"[^\n\r]+URI="([^"]+.m3u8[^"]*)"'
            needles = Regexer.do_regex(audio_needle, data)
            needle = r'(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}(?:[^\r\n]*AUDIO="([^"]+)"){0,1}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)'
            needles += Regexer.do_regex(needle, data)
            type_index = 0
            bitrate_index = 1
            id_index = 2
            url_index = 3
        else:
            needle = r"(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
            needles = Regexer.do_regex(needle, data)
            type_index = 0
            bitrate_index = 1
            url_index = 2

        audio_streams = {}
        base_url_logged = False
        base_url = base[:base.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.trace(n)

            if "#EXT-X-I-FRAME" in n[type_index]:
                continue

            if "://" not in n[url_index]:
                if not base_url_logged:
                    Logger.debug("Using baseUrl %s for M3u8", base_url)
                    base_url_logged = True
                stream = "%s/%s" % (base_url, n[url_index])
            else:
                if not base_url_logged:
                    Logger.debug("Full url found in M3u8")
                    base_url_logged = True
                stream = n[url_index]
            bitrate = n[bitrate_index]

            if qs is not None and stream.endswith("?null="):
                stream = stream.replace("?null=", "?%s" % (qs, ))
            elif qs is not None and "?" in stream:
                stream = "%s&%s" % (stream, qs)
            elif qs is not None:
                stream = "%s?%s" % (stream, qs)

            if map_audio and "#EXT-X-MEDIA" in n[type_index]:
                # noinspection PyUnboundLocalVariable
                Logger.debug("Found audio stream: %s -> %s", n[id_index], stream)
                audio_streams[n[id_index]] = stream
                continue

            if map_audio:
                streams.append((stream, bitrate, audio_streams.get(n[id_index]) or None))
            else:
                streams.append((stream, bitrate))

        Logger.debug("Found %s substreams in M3U8", len(streams))
        return streams
