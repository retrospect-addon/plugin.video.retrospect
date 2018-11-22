import mediaitem
import chn_class

from helpers import xmlhelper
from streams.youtube import YouTube
from urihandler import UriHandler
from helpers.datehelper import DateHelper
from logger import Logger


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "hardwareinfoimage.png"

        # setup the urls
        # self.mainListUri = "https://www.youtube.com/feeds/videos.xml?user=hardwareinfovideo"
        self.mainListUri = "http://nl.hardware.info/tv/rss-private/streaming"
        self.baseUrl = "http://www.youtube.com"

        # setup the main parsing data
        # self.episodeItemRegex = '<name>([^-]+) - (\d+)-(\d+)-(\d+)[^<]*</name>'
        # self._add_data_parser(self.mainListUri, preprocessor=self.AddEpisodePaging,
        #                     parser=self.episodeItemRegex, creator=self.create_episode_item)

        self.videoItemRegex = '<(?:entry|item)>([\w\W]+?)</(?:entry|item)>'
        self._add_data_parser("http://nl.hardware.info/tv/rss-private/streaming",
                              parser=self.videoItemRegex, creator=self.CreateVideoItemHwInfo,
                              updater=self.update_video_item)
        self._add_data_parser("*", parser=self.videoItemRegex, creator=self.create_video_item, updater=self.update_video_item)

        self.pageNavigationIndicationRegex = '<page>(\d+)</page>'
        self.pageNavigationRegex = '<page>(\d+)</page>'
        self.pageNavigationRegexIndex = 0
        self._add_data_parser("*", parser=self.pageNavigationRegex, creator=self.create_page_item)

        #===============================================================================================================
        # non standard items

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    def AddEpisodePaging(self, data):
        """Performs pre-process actions for data processing/

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        items = []

        # we need to create page items. So let's just spoof the paging. Youtube has
        # a 50 max results per query limit.
        itemsPerPage = 50
        data = UriHandler.open(self.mainListUri, proxy=self.proxy)
        xml = xmlhelper.XmlHelper(data)
        nrItems = xml.get_single_node_content("openSearch:totalResults")

        for index in range(1, int(nrItems), itemsPerPage):
            items.append(self.create_episode_item([index, itemsPerPage]))
            pass
        # Continue working normal!

        return data, items

    def create_episode_item(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        url = "http://gdata.youtube.com/feeds/api/users/hardwareinfovideo/uploads?max-results=%s&start-index=%s" % (
            resultSet[1], resultSet[0])
        title = "Hardware Info TV %04d-%04d" % (resultSet[0], resultSet[0] + resultSet[1])
        item = mediaitem.MediaItem(title, url)
        item.complete = True
        item.icon = self.icon
        item.thumb = self.noImage
        return item

    def create_video_item(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        xmlData = xmlhelper.XmlHelper(resultSet)

        title = xmlData.get_single_node_content("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        videoId = xmlData.get_single_node_content("id")
        lastSlash = videoId.rfind(":") + 1
        videoId = videoId[lastSlash:]
        # url = "http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=%s" % (videoId,)
        url = "http://www.youtube.com/watch?v=%s" % (videoId, )

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'video'

        # date stuff
        date = xmlData.get_single_node_content("published")
        year = date[0:4]
        month = date[5:7]
        day = date[8:10]
        hour = date[11:13]
        minute = date[14:16]
        # Logger.Trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.set_date(year, month, day, hour, minute, 0)

        # description stuff
        description = xmlData.get_single_node_content("media:description")
        item.description = description

        # thumbnail stuff
        thumbUrl = xmlData.get_tag_attribute("media:thumbnail", {'url': None}, {'height': '360'})
        # <media:thumbnail url="http://i.ytimg.com/vi/5sTMRR0_Wo8/0.jpg" height="360" width="480" time="00:09:52.500" xmlns:media="http://search.yahoo.com/mrss/" />
        if thumbUrl != "":
            item.thumb = thumbUrl
        else:
            item.thumb = self.noImage

        # finish up
        item.complete = False
        return item

    def CreateVideoItemHwInfo(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        xmlData = xmlhelper.XmlHelper(resultSet)

        title = xmlData.get_single_node_content("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        url = xmlData.get_tag_attribute("enclosure", {'url': None}, {'type': 'video/youtube'})
        Logger.trace(url)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'video'

        # date stuff
        date = xmlData.get_single_node_content("pubDate")
        dayname, day, month, year, time, zone = date.split(' ', 6)
        month = DateHelper.get_month_from_name(month, language="en")
        hour, minute, seconds = time.split(":")
        Logger.trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.set_date(year, month, day, hour, minute, 0)

        # # description stuff
        description = xmlData.get_single_node_content("description")
        item.description = description

        # # thumbnail stuff
        item.thumb = self.noImage
        thumbUrls = xmlData.get_tag_attribute("enclosure", {'url': None}, {'type': 'image/jpg'}, firstOnly=False)
        for thumbUrl in thumbUrls:
            if thumbUrl != "" and "thumb" not in thumbUrl:
                item.thumb = thumbUrl

        # finish up
        item.complete = False
        return item

    def update_video_item(self, item):
        """
        Accepts an arraylist of results. It returns an item.
        """

        part = item.create_new_empty_media_part()
        for s, b in YouTube.get_streams_from_you_tube(item.url, self.proxy):
            item.complete = True
            # s = self.get_verifiable_video_url(s)
            part.append_media_stream(s, b)

        item.complete = True
        return item
