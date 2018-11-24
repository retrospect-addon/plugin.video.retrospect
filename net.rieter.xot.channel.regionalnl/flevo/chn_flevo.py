import datetime
import mediaitem
import chn_class
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from helpers.jsonhelper import JsonHelper
from helpers.languagehelper import LanguageHelper
from logger import Logger
from parserdata import ParserData
from regexer import Regexer
from streams.m3u8 import M3u8
from urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # configure login stuff
        # setup the urls
        self.noImage = "flevoimage.png"
        self.mainListUri = "https://www.omroepflevoland.nl/block/missed/list?category=Gemist&page=1"
        # self.mainListUri = "https://www.omroepflevoland.nl/block/missed/list?category=Gemist&type=televisie&page=1"
        self.baseUrl = "https://www.omroepflevoland.nl"
        self.channelBitrate = 780

        videoItemRegex = '<a[^>]+href="(?<url>[^"]+)"(?:[^>]+>\W*){2}<div[^>]+background-image: url\(\'(?<thumburl>[^\']+)\'[^>]+>(?:[^>]+>){7}\W*<h5>(?<title>[^<]+)<[^>]*>\s*(?<date>\d+-\d+-\d+\s+\d+:\d+)(?:[^>]+>){11}\W*(?<description>[^<]+)</p>'
        videoItemRegex = Regexer.from_expresso(videoItemRegex)

        self._add_data_parser(self.mainListUri, preprocessor=self.AddLiveStreams,
                              parser=videoItemRegex, creator=self.create_video_item)

        self._add_data_parser("https://[^/]*.cloudfront.net/live/", updater=self.UpdateLiveUrls,
                              match_type=ParserData.MatchRegex)

        self._add_data_parser("*", preprocessor=self.AddLiveStreams,
                              parser=videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveStreams(self, data):
        """ Parses the xml data entry of the mainlist

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
        if self.parentItem is None:
            liveItem = mediaitem.MediaItem(
                "\a.: Live TV :.",
                "https://d5ms27yy6exnf.cloudfront.net/live/omroepflevoland/tv/index.m3u8"
            )
            liveItem.icon = self.icon
            liveItem.thumb = self.noImage
            liveItem.type = 'video'
            liveItem.dontGroup = True
            now = datetime.datetime.now()
            liveItem.set_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
            items.append(liveItem)

            liveItem = mediaitem.MediaItem(
                "\a.: Live Radio :.",
                "https://d5ms27yy6exnf.cloudfront.net/live/omroepflevoland/radio/index.m3u8"
            )
            liveItem.icon = self.icon
            liveItem.thumb = self.noImage
            liveItem.type = 'video'
            liveItem.dontGroup = True
            now = datetime.datetime.now()
            liveItem.set_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
            items.append(liveItem)

        # add "More"
        more = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        currentUrl = self.parentItem.url if self.parentItem is not None else self.mainListUri
        url, page = currentUrl.rsplit("=", 1)
        url = "{}={}".format(url, int(page) + 1)

        item = mediaitem.MediaItem(more, url)
        item.thumb = self.noImage
        item.icon = self.icon
        item.fanart = self.fanart
        item.complete = True
        items.append(item)

        return data, items

    def create_video_item(self, resultSet):
        item = chn_class.Channel.create_video_item(self, resultSet)
        if item is None:
            return item

        timeStamp = DateHelper.get_date_from_string(resultSet["date"], "%d-%m-%Y %H:%M")
        item.set_date(*timeStamp[0:6])
        return item

    def update_video_item(self, item):
        data = UriHandler.open(item.url, proxy=self.proxy)
        jsonData = Regexer.do_regex("video.createPlayer\(JSON.parse\('([^']+)", data)[0]
        jsonData = jsonData.decode('unicode-escape').encode('ascii')
        jsonData = jsonData.replace("\\\\", "")
        json = JsonHelper(jsonData)
        stream = json.get_value("file")
        if not stream:
            return item

        part = item.create_new_empty_media_part()
        if ".mp3" in stream:
            item.complete = True
            part.append_media_stream(stream, 0)
        elif stream.endswith(".mp4"):
            item.complete = True
            part.append_media_stream(stream, 2500)
        elif ".m3u8" in stream:
            item.url = stream
            return self.UpdateLiveUrls(item)
        return item

    def UpdateLiveUrls(self, item):
        """Updates an existing MediaItem with more data.

        Arguments:
        item : MediaItem - the MediaItem that needs to be updated

        Returns:
        The original item with more data added to it's properties.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            stream = part.append_media_stream(item.url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy)
            item.complete = True
        else:

            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, b)
            item.complete = True
        return item
