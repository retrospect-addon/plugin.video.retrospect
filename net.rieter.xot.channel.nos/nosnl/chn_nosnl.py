import mediaitem
import chn_class
import time

from helpers.jsonhelper import JsonHelper
from helpers.encodinghelper import EncodingHelper

from logger import Logger
from urihandler import UriHandler


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
        self.noImage = "nosnlimage.png"

        # setup the urls
        # self.mainListUri = "http://nos.nl/"
        self.mainListUri = "#getcategories"

        # we need specific headers: APK:NosHttpClientHelper.java
        salt = int(time.time())
        key = "%sRM%%j%%l@g@w_A%%" % (salt,)
        Logger.Trace("Found Salt: %s and Key: %s", salt, key)
        key = EncodingHelper.EncodeMD5(key, toUpper=False)
        self.httpHeaders = {"X-NOS-App": "Google/x86;Android/4.4.4;nl.nos.app/3.1",
                            "X-NOS-Salt": salt,
                            "X-NOS-Key": key}

        self.baseUrl = "http://nos.nl"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, preprocessor=self.GetCategories)
        self._AddDataParser("*", preprocessor=self.AddNextPage, json=True,
                            parser=(), creator=self.CreateJsonVideo, updater=self.UpdateJsonVideo)

        self._AddDataParser("http://content.nos.nl/apps/feeds/most-watched-video/", json=True,
                            preprocessor=self.AddNextPage,
                            parser=('items',), creator=self.CreateJsonVideo, updater=self.UpdateJsonVideo)

        #===============================================================================================================
        # non standard items
        # self.__IgnoreCookieLaw()

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddNextPage(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the ProcessFolderList method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """
        items = []

        # we need to add a "more" item
        url = self.parentItem.url
        url, page = url.rsplit("/", 1)
        url = "%s/%s" % (url, int(page) + 1)
        moreItem = mediaitem.MediaItem("Meer", url)
        moreItem.HttpHeaders = self.httpHeaders
        moreItem.thumb = self.parentItem.thumb
        moreItem.dontGroup = True
        moreItem.complete = True
        items.append(moreItem)

        return data, items

    def GetCategories(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the ProcessFolderList method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.Info("Creating categories")
        items = []

        cats = {"Meest Bekeken": "http://content.nos.nl/apps/feeds/most-watched-video/page/1",
                "Nieuws": "http://content.nos.nl/apps/feeds/video/maincategory/nieuws/page/1",
                "Sport": "http://content.nos.nl/apps/feeds/video/maincategory/sport/page/1",
                "Alles": "http://content.nos.nl/apps/feeds/video/page/1", }

        for cat in cats:
            item = mediaitem.MediaItem(cat, cats[cat])
            item.thumb = self.noImage
            item.icon = self.icon
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            items.append(item)

        Logger.Debug("Creating categories finished")
        return data, items

    def CreateJsonVideo(self, resultSet):
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
        self.UpdateVideoItem method is called if the item is focussed or selected
        for playback.

        """

        # Logger.Trace(JsonHelper.DictionaryToString(resultSet))

        videoId = resultSet['id']
        # category = resultSet["maincategory"].title()
        # subcategory = resultSet["subcategory"].title()

        url = "http://content.nos.nl/apps/video/%s/format/mp4-web01" % (videoId, )
        if "http:" not in url:
            url = "%s/%s" % (self.baseUrl, url)

        item = mediaitem.MediaItem(resultSet['title'], url, type="video")
        item.icon = self.icon
        item.thumb = resultSet['image'].replace("*size*", "xl")
        item.description = resultSet["description"]
        item.HttpHeaders = self.httpHeaders
        item.complete = False

        # set the date and time
        date = resultSet["pub_date"]
        date, time, ignore = date.split(" ", 2)
        day, month, year = date.split("-")
        hour, minutes, seconds = time.split(":")
        item.SetDate(year, month, day, hour, minutes, seconds)
        return item

    def UpdateJsonVideo(self, item):
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

        Logger.Debug('Starting UpdateVideoItem: %s', item.name)

        qualities = {"mp4-web03": 1200, "mp4-web01": 500}  # , "http-hls": 1500, "3gp-mob01": 300, "flv-web01": 500}
        part = item.CreateNewEmptyMediaPart()
        for q in qualities:
            url = item.url.replace("mp4-web01", q)
            data = UriHandler.Open(url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
            if not data:
                Logger.Warning("No data found for: %s", q)
                continue
            json = JsonHelper(data, logger=Logger.Instance())
            url = json.GetValue("url")
            part.AppendMediaStream(url, qualities[q])
        item.complete = True
        return item

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # a second cookie seems to be required
        UriHandler.SetCookie(name='npo_cc', value='tmp', domain='.nos.nl')
        return
