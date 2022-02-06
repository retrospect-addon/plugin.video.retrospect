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
            self.mainListUri = "https://slam.nl"
            self.baseUrl = "http://www.slam.nl"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.add_live_streams)

        # updater for live streams
        self._add_data_parsers(["https://hls.slam.nl/streaming/hls/"],
                               updater=self.update_live_stream_m3u8)

        self._add_data_parser("https://playerservices.streamtheworld.com/api/livestream-redirect",
                              updater=self.update_live_stream_redirect)

        # ===========================================================================================
        # non standard items

        # ===========================================================================================
        # Test cases:

        # ============================= Actual channel setup STOPS here =============================

    def add_live_streams(self, data):

        items = []

        slam_fm = MediaItem("Slam!", "http://22553.live.streamtheworld.com/SLAM_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! 40", "https://25343.live.streamtheworld.com/WEB14_MP3_SC"
                                        "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                                        "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! Nonstop", "https://22323.live.streamtheworld.com/WEB10_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! The Boom Room", "https://20873.live.streamtheworld.com/WEB12_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! 00s", "https://22713.live.streamtheworld.com/WEB15_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! Juize", "https://22543.live.streamtheworld.com/WEB09_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! MixMarathon", "https://stream.slam.nl/web13_mp3"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! Hardstyle", "https://22323.live.streamtheworld.com/WEB11_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)

        slam_fm = MediaItem("Slam! Housuh in de Pauzuh", "http://22553.live.streamtheworld.com/SLAM_MP3_SC"
                            "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                            "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)
        return data, items

        Logger.trace(result_set)

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

        for s, b in M3u8.set_input_stream_addon_input(item.url):
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
