import string

import mediaitem
import chn_class

from helpers import datehelper
from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from xbmcwrapper import XbmcWrapper
from helpers.encodinghelper import EncodingHelper
from helpers.jsonhelper import JsonHelper
from streams.youtube import YouTube


class Channel(chn_class.Channel):

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "dumpertimage.png"

        # setup the urls
        self.baseUrl = "http://www.dumpert.nl/mediabase/flv/%s_YTDL_1.flv.flv"

        # setup the main parsing data
        self.mainListUri = "#mainlist"
        self._add_data_parser(self.mainListUri, preprocessor=self.GetMainListItems)
        self.videoItemRegex = '<a[^>]+href="([^"]+)"[^>]*>\W+<img src="([^"]+)[\W\w]{0,400}<h\d>([^<]+)</h\d>\W+<[^>]' \
                              '*date"{0,1}>(\d+) (\w+) (\d+) (\d+):(\d+)'
        self._add_data_parser("*",
                              parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # ====================================== Actual channel setup STOPS here =======================================
        self.__IgnoreCookieLaw()
        return

    def GetMainListItems(self, data):
        """ 
        accepts an url and returns an list with items of type CListItem
        Items have a name and url. This is used for the filling of the progwindow
        """

        items = []
        urlPattern = "http://www.dumpert.nl/%s/%s/"

        for page in range(1, 3):
            item = mediaitem.MediaItem("Toppertjes - Pagina %s" % (page, ), urlPattern % ('toppers', page))
            item.icon = self.icon
            items.append(item)

        for page in range(1, 11):
            item = mediaitem.MediaItem("Filmpjes - Pagina %s" % (page, ), urlPattern % ('filmpjes', page))
            item.icon = self.icon
            items.append(item)

        item = mediaitem.MediaItem("Zoeken", "searchSite")
        item.icon = self.icon
        items.append(item)

        return data, items

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

        #                         0              1             2                             3
        #<a class="item" href="([^"]+)"[^=]+="([^"]+)" alt="([^"]+)[^:]+<div class="date">([^<]+)

        #Logger.Trace(resultSet)

        item = mediaitem.MediaItem(resultSet[2], resultSet[0], type='video')
        item.icon = self.icon
        item.description = resultSet[2]
        item.thumb = resultSet[1]

        try:
            month = datehelper.DateHelper.get_month_from_name(resultSet[4], "nl")
            item.set_date(resultSet[5], month, resultSet[3], resultSet[6], resultSet[7], 0)
        except:
            Logger.error("Error matching month: %s", resultSet[4].lower(), exc_info=True)

        item.complete = False
        return item

    def update_video_item(self, item):
        """
        Updates the item
        """

        data = UriHandler.open(item.url, proxy=self.proxy)
        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        baseEncode = Regexer.do_regex('data-files="([^"]+)', data)
        if baseEncode:
            Logger.debug("Loading video from BASE64 encoded JSON data")
            baseEncode = baseEncode[-1]
            jsonData = EncodingHelper.decode_base64(baseEncode)
            json = JsonHelper(jsonData, logger=Logger.instance())
            Logger.trace(json)

            # "flv": "http://media.dumpert.nl/flv/e2a926ff_10307954_804223649588516_151552487_n.mp4.flv",
            # "tablet": "http://media.dumpert.nl/tablet/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",
            # "mobile": "http://media.dumpert.nl/mobile/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",

            streams = json.get_value()
            for key in streams:
                if key == "flv":
                    part.append_media_stream(streams[key], 1000)
                elif key == "720p":
                    part.append_media_stream(streams[key], 1200)
                elif key == "1080p":
                    part.append_media_stream(streams[key], 1600)
                elif key == "tablet":
                    part.append_media_stream(streams[key], 800)
                elif key == "mobile":
                    part.append_media_stream(streams[key], 450)
                elif key == "embed" and streams[key].startswith("youtube"):
                    embedType, youtubeId = streams[key].split(":")
                    url = "https://www.youtube.com/watch?v=%s" % (youtubeId, )
                    for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                else:
                    Logger.debug("Key '%s' was not used", key)
            item.complete = True
            Logger.trace("VideoItem updated: %s", item)
            return item

        youtubeId = Regexer.do_regex("class='yt-iframe'[^>]+src='https://www.youtube.com/embed/([^?]+)", data)
        if youtubeId:
            youtubeId = youtubeId[-1]
            url = "https://www.youtube.com/watch?v=%s" % (youtubeId,)
            for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        return item

    def search_site(self, url=None):
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        items = []

        needle = XbmcWrapper.show_key_board()
        if needle:
            #convert to HTML
            needle = string.replace(needle, " ", "%20")
            searchUrl = "http://www.dumpert.nl/search/V/%s/ " % (needle, )
            temp = mediaitem.MediaItem("Search", searchUrl)
            return self.process_folder_list(temp)

        return items

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.dumpert.nl")

        # Set-Cookie: cpc=10; path=/; domain=www.dumpert.nl; expires=Thu, 11-Jun-2020 18:49:38 GMT
        UriHandler.set_cookie(name='cpc', value='10', domain='.www.dumpert.nl')
        return
