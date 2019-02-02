import chn_class

from mediaitem import MediaItem
from helpers.jsonhelper import JsonHelper
from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from streams.m3u8 import M3u8


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
        self.noImage = "atvimage.png"

        # setup the urls
        self.mainListUri = "http://www.atv.sr/on-demand/"
        self.baseUrl = "http://www.atv.sr"
        self.swfUrl = "http://www.tikilive.com/public/player/player.flash.swf"

        # setup the intial listing
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, preprocessor=self.add_live,
                              parser=r'<h3>([^>]+)</h3>[\w\W]+?<a[^>]+href\W+"([^"]+)"[^>]*>meer',
                              creator=self.create_episode_item)

        # videos on the main list
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=r'<a title="(Suri[^"]+|Whaz[^"]+)" href="([^"]+)" rel="bookmark">\W+<img[^>]*src="([^"]+)',
                              creator=self.create_video_item)

        self._add_data_parser("*",
                              parser=r'<a[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\W+<img[^>]*src="([^"]+)"',
                              creator=self.create_video_item, updater=self.update_video_item)

        self._add_data_parser("http://cache.tikilive.com:8080/socket.io/",
                              updater=self.update_live_item)
        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live(self, data):
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

        Logger.info("Performing Pre-Processing")
        items = []

        item = MediaItem("\a.: Live TV :.", "http://cache.tikilive.com:8080/socket.io/"
                                            "?c=34967&n=TIKISESSID&i=fo84il3e7qs68uet2ql2eav081&EIO=3"
                                            "&transport=polling&t=1428225927102-0")
        item.type = 'video'
        item.dontGroup = True
        item.isLive = True
        items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if result_set[0]:
            title = result_set[0]
            url = result_set[1]
        else:
            title = result_set[2]
            url = result_set[3]

        item = MediaItem(title, url)
        item.thumb = self.noImage
        item.icon = self.icon
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
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        item = MediaItem(result_set[0], result_set[1])
        item.thumb = self.noImage
        item.icon = self.icon
        item.type = 'video'
        item.thumb = result_set[2]
        item.complete = False
        return item

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy)
        streams = Regexer.do_regex('<(?:source|video)[^>]+src="([^"]+)"[^>]+>', data)
        part = item.create_new_empty_media_part()
        for s in streams:
            part.append_media_stream(s.replace(" ", "%20"), 0)

        item.complete = True
        return item

    def update_live_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy)
        data = data[data.index('{'):]
        json = JsonHelper(data)

        sid = json.get_value("sid")
        # The i= is the same as the one from the RTMP stream at the page of ATV.sr:
        # http://edge1.tikilive.com:1935/rtmp_tikilive/34967/amlst:mainstream/jwplayer.smil?id=dIzAVAVL2dirCfJgAPEb&i=YXBwTmFtZT1QbGF5ZXImY0lEPTM0OTY3JmNOYW1lPUFUViUyME5ldHdvcmtzJm9JRD0xMzY1NTUmb05hbWU9YXR2bmV0d29ya3Mmc0lkPWJwaHR2bXR2OXI4M2N1Mm9sZ2Q5dWx1aWs2JnVJRD0wJnVOYW1lPUd1ZXN0OWFmYTE=

        video_url = "http://edge2.tikilive.com:1935/html5_tikilive/34967/amlst:mainstream/playlist.m3u8" \
                    "?i=YXBwTmFtZT1QbGF5ZXImY0lEPTM0OTY3JmNOYW1lPUFUViUyME5ldHdvcmtzJm9JRD0xMzY1NTUmb05hbW" \
                    "U9YXR2bmV0d29ya3Mmc0lkPWZvODRpbDNlN3FzNjh1ZXQycWwyZWF2MDgxJnVJRD0wJnVOYW1lPUd1ZXN0MTNiNjk=&id=%s" \
                    % (sid,)
        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(video_url, self.proxy):
            item.complete = True
            part.append_media_stream(s, b)

        item.complete = True
        return item
