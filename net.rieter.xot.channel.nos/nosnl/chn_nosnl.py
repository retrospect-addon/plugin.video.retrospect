import mediaitem
import chn_class
import time
import base64

from helpers.jsonhelper import JsonHelper
from helpers.encodinghelper import EncodingHelper
from helpers.datehelper import DateHelper
from helpers.languagehelper import LanguageHelper

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
        # key = "%sRM%%j%%l@g@w_A%%" % (salt,)
        # Logger.Trace("Found Salt: %s and Key: %s", salt, key)
        # key = EncodingHelper.EncodeMD5(key, toUpper=False)
        # self.httpHeaders = {"X-NOS-App": "Google/x86;Android/4.4.4;nl.nos.app/3.1",
        #                     "X-NOS-Salt": salt,
        #                     "X-NOS-Key": key}

        userAgent = "%s;%d;%s/%s;Android/%s;nl.nos.app/%s" % ("nos", salt, "Google", "Nexus", "6.0", "5.1.1")
        string = ";UB}7Gaji==JPHtjX3@c%s" % (userAgent, )
        string = EncodingHelper.EncodeMD5(string, toUpper=False).zfill(32)
        xnos = string + base64.b64encode(userAgent)
        self.httpHeaders = {"X-Nos": xnos}

        self.baseUrl = "http://nos.nl"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, preprocessor=self.GetCategories)
        self._AddDataParser("*",
                            # preprocessor=self.AddNextPage,
                            json=True,
                            parser=('items', ),
                            creator=self.CreateJsonVideo, updater=self.UpdateJsonVideo)
        self._AddDataParser("*",
                            json=True,
                            parser=('links',),
                            creator=self.CreatePageItem)

        #===============================================================================================================
        # non standard items
        # self.__IgnoreCookieLaw()
        self.__pageSize = 50

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        cats = {
            "Meest Bekeken": "https://api.nos.nl/mobile/videos/most-viewed/phone.json",
            "Nieuws": "https://api.nos.nl/nosapp/v3/items?mainCategories=nieuws&types=video&limit={0}".format(self.__pageSize),
            "Sport": "https://api.nos.nl/nosapp/v3/items?mainCategories=sport&types=video&limit={0}".format(self.__pageSize),
            "Alles": "https://api.nos.nl/nosapp/v3/items?types=video&limit={0}".format(self.__pageSize),
        }

        for cat in cats:
            item = mediaitem.MediaItem(cat, cats[cat])
            item.thumb = self.noImage
            item.icon = self.icon
            item.complete = True
            items.append(item)

        Logger.Debug("Creating categories finished")
        return data, items

    def CreatePageItem(self, resultSet):
        items = []
        if 'next' in resultSet:
            title = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)
            url = resultSet['next']
            item = mediaitem.MediaItem(title, url)
            item.fanart = self.parentItem.fanart
            item.thumb = self.parentItem.thumb
            items.append(item)

        return items

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

        url = "https://api.nos.nl/mobile/video/%s/phone.json" % (videoId, )
        item = mediaitem.MediaItem(resultSet['title'], url, type="video")
        item.icon = self.icon
        if 'image' in resultSet:
            images = resultSet['image']["formats"]
            matchedImage = images[-1]
            for image in images:
                if image["width"] >= 720:
                    matchedImage = image
                    break
            item.thumb = matchedImage["url"].values()[0]

        item.description = resultSet["description"]
        item.complete = False
        item.isGeoLocked = resultSet.get("geoprotection", False)

        # set the date and time
        date = resultSet["published_at"]
        timeStamp = DateHelper.GetDateFromString(date, dateFormat="%Y-%m-%dT%H:%M:%S+{0}".format(date[-4:]))
        item.SetDate(*timeStamp[0:6])
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

        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=self.httpHeaders)
        jsonData = JsonHelper(data)
        streams = jsonData.GetValue("formats")
        if not streams:
            return item

        qualities = {"480p": 1200, "360p": 500, "other": 0}  # , "http-hls": 1500, "3gp-mob01": 300, "flv-web01": 500}
        part = item.CreateNewEmptyMediaPart()
        for stream in streams:
            part.AppendMediaStream(
                url=stream["url"].values()[-1],
                bitrate=qualities[stream.get("name", "other")]
            )

        item.complete = True
        return item

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # a second cookie seems to be required
        UriHandler.SetCookie(name='npo_cc', value='tmp', domain='.nos.nl')
        return
