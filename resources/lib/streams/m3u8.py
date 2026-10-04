# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer


class M3u8(object):
    def __init__(self):
        pass

    @staticmethod
    def get_subtitle(url, play_list_data=None, append_query_string=True, language=None):  # NOSONAR
        """ Retrieves a subtitle url either from a M3u8 file via HTTP or alternatively from a
        M3u8 playlist string value (in case it was already retrieved).

        :param str url:                     The M3u8 url that contains   the subtitle information.
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

    # @staticmethod
    # def get_streams_from_m3u8(url,  # NOSONAR
    #                           headers=None,
    #                           append_query_string=False,
    #                           map_audio=False,
    #                           play_list_data=None):
    #     """ Parsers standard M3U8 lists and returns a list of tuples with streams and bitrates that
    #     can be used by other methods.
    #
    #     Can be used like this:
    #
    #         for s, b in M3u8.get_streams_from_m3u8(m3u8_url):
    #             item.complete = True
    #             # s = self.get_verifiable_video_url(s)
    #             item.add_stream(s, b)
    #
    #     :param dict[str,str] headers:       Possible HTTP Headers
    #     :param str url:                     The url to download
    #     :param bool append_query_string:    Should the existing query string be appended?
    #     :param bool map_audio:              Map audio streams
    #     :param str play_list_data:          Data of an already retrieved M3u8
    #
    #     :return: a list of streams with their bitrate and optionally the audio streams.
    #     :rtype: list[tuple[str,str]|tuple[str,str,str]]
    #
    #     """
    #
    #     streams = []
    #
    #     data = play_list_data or UriHandler.open(url, additional_headers=headers)
    #     Logger.trace(data)
    #
    #     qs = None
    #     if append_query_string and "?" in url:
    #         base, qs = url.split("?", 1)
    #         Logger.info("Going to append QS: %s", qs)
    #     elif "?" in url:
    #         base, qs = url.split("?", 1)
    #         Logger.info("Ignoring QS: %s", qs)
    #         qs = None
    #     else:
    #         base = url
    #
    #     Logger.debug("Processing M3U8 Streams: %s", url)
    #
    #     # If we need audio
    #     if map_audio:
    #         audio_needle = r'(#\w[^:]+):TYPE=AUDIO()[^\r\n]+ID="([^"]+)"[^\n\r]+URI="([^"]+.m3u8[^"]*)"'
    #         needles = Regexer.do_regex(audio_needle, data)
    #         needle = r'(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}(?:[^\r\n]*AUDIO="([^"]+)"){0,1}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)'
    #         needles += Regexer.do_regex(needle, data)
    #         type_index = 0
    #         bitrate_index = 1
    #         id_index = 2
    #         url_index = 3
    #     else:
    #         needle = r"(#\w[^:]+)[^\n]+BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
    #         needles = Regexer.do_regex(needle, data)
    #         type_index = 0
    #         bitrate_index = 1
    #         url_index = 2
    #
    #     audio_streams = {}
    #     base_url_logged = False
    #     base_url = base[:base.rindex("/")]
    #     for n in needles:
    #         # see if we need to append a server path
    #         Logger.trace(n)
    #
    #         if "#EXT-X-I-FRAME" in n[type_index]:
    #             continue
    #
    #         if "://" not in n[url_index]:
    #             if not base_url_logged:
    #                 Logger.debug("Using baseUrl %s for M3u8", base_url)
    #                 base_url_logged = True
    #             stream = "%s/%s" % (base_url, n[url_index])
    #         else:
    #             if not base_url_logged:
    #                 Logger.debug("Full url found in M3u8")
    #                 base_url_logged = True
    #             stream = n[url_index]
    #         bitrate = n[bitrate_index]
    #
    #         if qs is not None and stream.endswith("?null="):
    #             stream = stream.replace("?null=", "?%s" % (qs, ))
    #         elif qs is not None and "?" in stream:
    #             stream = "%s&%s" % (stream, qs)
    #         elif qs is not None:
    #             stream = "%s?%s" % (stream, qs)
    #
    #         if map_audio and "#EXT-X-MEDIA" in n[type_index]:
    #             # noinspection PyUnboundLocalVariable
    #             Logger.debug("Found audio stream: %s -> %s", n[id_index], stream)
    #             audio_streams[n[id_index]] = stream
    #             continue
    #
    #         if map_audio:
    #             streams.append((stream, bitrate, audio_streams.get(n[id_index]) or None))
    #         else:
    #             streams.append((stream, bitrate))
    #
    #     Logger.debug("Found %s substreams in M3U8", len(streams))
    #     return streams
