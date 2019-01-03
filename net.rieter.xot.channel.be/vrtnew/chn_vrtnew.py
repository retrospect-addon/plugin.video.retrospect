# coding:Cp1252

import chn_class

from parserdata import ParserData
from regexer import Regexer
from logger import Logger
from streams.m3u8 import M3u8
from urihandler import UriHandler
from mediaitem import MediaItem


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        if self.channelCode == "redactie":
            self.noImage = "redactieimage.jpg"
            self.mainListUri = "http://deredactie.be/cm/vrtnieuws/videozone"
            self.baseUrl = "http://deredactie.be"

        else:
            raise IndexError("Invalid Channel Code")  # setup the urls

        self.swfUrl = "%s/html/flash/common/player.5.10.swf" % (self.baseUrl,)

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=r'<li[^>]*>\W*<a href="(/cm/[^"]+/videozone/programmas/[^"]+)'
                                     r'" title="([^"]+)"\W*>',
                              creator=self.create_episode_item)

        self._add_data_parser("*", creator=self.create_video_item,
                              parser=r'<a href="(/cm/[^/]+/videozone/programmas/[^?"]+)"[^>]*>\W*'
                                     r'<span[^>]+>([^<]+)</span>\W*(?:<span[^<]+</span>\W*){0,2}'
                                     r'<span class="video">\W*<img src="([^"]+)"')
        self._add_data_parser("*", creator=self.create_video_item,
                              parser=r'data-video-permalink="([^"]+)"[^>]*>\W+<span[^>]*>([^<]+)'
                                     r'</span>\W+<span[^>]*>\W+<img[^>]*src="([^"]+)"',
                              updater=self.update_video_item)

        self._add_data_parser("*", creator=self.create_page_item,
                              parser=r'<a href="([^"]+\?page=\d+)"[^>]+>(\d+)')
        self.pageNavigationRegexIndex = 1

        self.mediaUrlRegex = r'data-video-((?:src|rtmp|iphone|mobile)[^=]*)="([^"]+)"\W+' \
                             r'(?:data-video-[^"]+path="([^"]+)){0,1}'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def pre_process_folder_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        # Only get the first bit
        seperator_index = data.find('<div class="splitter split24">')
        data = data[:seperator_index]
        return chn_class.Channel.pre_process_folder_list(self, data)

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|none

        """

        url = "%s%s" % (self.baseUrl, result_set[0])
        name = result_set[1]

        item = MediaItem(name.capitalize(), url)
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|none

        """

        Logger.trace(result_set)
        item = None
        # not implemented yet
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|none

        """

        Logger.trace(result_set)

        name = result_set[1]
        url = result_set[0]
        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, result_set[0])

        if len(result_set) == 3:
            thumb = result_set[2]
        else:
            thumb = ""

        if thumb and not thumb.startswith("http://"):
            thumb = "%s%s" % (self.baseUrl, thumb)

        item = MediaItem(name, url)
        item.thumb = thumb
        item.description = name
        item.icon = self.icon
        item.type = 'video'
        item.complete = False

        name_parts = name.rsplit("/", 3)
        if len(name_parts) == 3:
            Logger.debug("Found possible date in name: %s", name_parts)
            year = name_parts[2]
            if len(year) == 2:
                year = 2000 + int(year)
            month = name_parts[1]
            day = name_parts[0].rsplit(" ", 1)[1]
            Logger.trace("%s - %s - %s", year, month, day)
            item.set_date(year, month, day)

        return item

    def update_video_item(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
        data-video-id="1613274"
        data-video-type="video"
        data-video-src="http://media.vrtnieuws.net/2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-title="Het journaal 1 - 25/04/13"
        data-video-rtmp-server="rtmp://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmp-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-rtmpt-server="rtmpt://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmpt-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-iphone-server="http://iphone.streampower.be/vrtnieuws_nogeo/_definst_"
        data-video-iphone-path="2013/04/135132051ONL1304255866693.urlMP4_H.264.m4v"
        data-video-mobile-server="rtsp://mp4.streampower.be/vrt/vrt_mobile/vrtnieuws_nogeo"
        data-video-mobile-path="2013/04/135132051ONL1304255866693.url3GP_MPEG4.3gp"
        data-video-sitestat-program="het_journaal_1_-_250413_id_1-1613274"
        """

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url)

        descriptions = Regexer.do_regex('<div class="longdesc"><p>([^<]+)</', data)
        Logger.trace(descriptions)
        for desc in descriptions:
            item.description = desc

        data = data.replace("\\/", "/")
        urls = Regexer.do_regex(self.mediaUrlRegex, data)
        part = item.create_new_empty_media_part()
        for url in urls:
            Logger.trace(url)
            if url[0] == "src":
                flv = url[1]
                bitrate = 750
            else:
                flv_server = url[1]
                flv_path = url[2]

                if url[0] == "rtmp-server":
                    flv = "%s//%s" % (flv_server, flv_path)
                    bitrate = 750

                elif url[0] == "iphone-server":
                    flv = "%s/%s" % (flv_server, flv_path)
                    if not flv.endswith("playlist.m3u8"):
                        flv = "%s/playlist.m3u8" % (flv,)

                    for s, b in M3u8.get_streams_from_m3u8(flv, self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                    # no need to continue adding the streams
                    continue

                elif url[0] == "mobile-server":
                    flv = "%s/%s" % (flv_server, flv_path)
                    bitrate = 250

                else:
                    flv = "%s/%s" % (flv_server, flv_path)
                    bitrate = 0

            part.append_media_stream(flv, bitrate)

        item.complete = True
        return item
