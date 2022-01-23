# SPDX-License-Identifier: GPL-3.0-or-later

import datetime

from resources.lib import chn_class, mediatype
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """Initialisation of the class.

        Arguments:
        channel_info: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = ""

        # setup the urls
        if self.channelCode == 'slam':
            self.noImage = "slam.png"
            self.mainListUri = "https://content.talparad.io/spaces/3p0bn61n86ty/environments/master/entries?content_type=overview&fields.slug=programmas&include=4"
            self.baseUrl = "http://www.slam.nl"
            self.swfUrl = "http://www.538.nl/jwplayer/player.swf" #I am not sure what this is
            

         # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              json=True, preprocessor=self.make_episode_dictionary_array,
                              parser=["items", ], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["items", "tracklist"], creator=self.create_music_item,
                              updater=self.update_music_item)

        # self._add_data_parser("https://playerservices.streamtheworld.com/api/livestream",
        #                       updater=self.update_live_stream_xml)

        #===========================================================================================
        # non standard items

        #===========================================================================================
        # Test cases:

        #============================= Actual channel setup STOPS here =============================
        return

        items = []

        slam_fm = MediaItem("Slam!", "http://22553.live.streamtheworld.com/SLAM_MP3_SC"
                                        "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                                        "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)
        return data, items


        slam_fm = MediaItem("Slam! Hardstyle", "https://22323.live.streamtheworld.com/WEB11_MP3_SC"
                                        "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                                        "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)
        return data, items

    def create_api_station(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        items = []

        title = result_set['title']
        stream_types = result_set["media"]
        for stream in stream_types:
            url = stream["uri"]
            if not url.startswith("http"):
                continue

            source = stream["source"]

            if "video" in source:
                item = MediaItem(
                    "{} Video".format(title), url, media_type=mediatype.VIDEO)
                item.isLive = True
                items.append(item)

            else:
                item = MediaItem(
                    title, url, media_type=mediatype.AUDIO)
                items.append(item)

            Logger.debug("Found stream for %s: %s (%s)", title, url, source)

        return items


    def update_live_stream_m3u8(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        for s, b in M3u8.get_streams_from_m3u8(item.url):
            item.complete = True
            item.add_stream(s, b)

        item.complete = True
        return item

    def update_live_stream_redirect(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        _, url = UriHandler.header(item.url)
        item.add_stream(url.replace(".mp3", ""))
        item.complete = True
        return item
