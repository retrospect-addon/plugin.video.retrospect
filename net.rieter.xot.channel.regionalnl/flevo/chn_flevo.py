import datetime
import mediaitem
import chn_class
from regexer import Regexer
from urihandler import UriHandler
from logger import Logger
from helpers.xmlhelper import XmlHelper
from streams.m3u8 import M3u8


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
        self.mainListUri = "#parsexml"
        self.baseUrl = "http://www.omroepflevoland.nl"
        self.channelBitrate = 780

        self._AddDataParser(self.mainListUri, preprocessor=self.ParseXmlData)
        self._AddDataParser("http://edge02.streamgate.nl", updater=self.UpdateLiveUrls)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    def ParseXmlData(self, data):
        """ Parses the xml data entry of the mainlist

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
        data = UriHandler.Open("http://www.omroepflevoland.nl/Mobile/FeedV3/programmas.aspx?t=a&wifi=1&v=14",
                               proxy=self.proxy)
        programs = Regexer.DoRegex("<item[\w\W]{0,5000}?</item>", data)

        liveItem = mediaitem.MediaItem("\a.: Live TV :.", "http://edge02.streamgate.nl/live/omroepflevoland/"
                                                          "smil:flevo_livestream.smil/playlist.m3u8")
        liveItem.icon = self.icon
        liveItem.thumb = self.noImage
        liveItem.type = 'video'
        liveItem.dontGroup = True
        now = datetime.datetime.now()
        liveItem.SetDate(now.year, now.month, now.day, now.hour, now.minute, now.second)
        items.append(liveItem)

        for program in programs:
            xmlData = XmlHelper(program)
            name = xmlData.GetTagAttribute("item", {"title": None})
            Logger.Debug("Processing: '%s'", name)

            thumb = xmlData.GetTagAttribute("thumb", {"url": None})
            thumb = "http://www.omroepflevoland.nl/SiteFiles/%s" % (thumb, )

            date = xmlData.GetTagAttribute("item", {"date": None})
            day, month, year = date.split("-")

            showItem = mediaitem.MediaItem(name, None)
            showItem.thumb = thumb
            showItem.icon = self.icon
            showItem.SetDate(year, month, day)
            items.append(showItem)

            episodes = Regexer.DoRegex("<show[\w\W]{0,1000}?</show>", program)
            for episode in episodes:
                xmlData = XmlHelper(episode)
                url = xmlData.GetTagAttribute("show", {"url": None})
                description = xmlData.GetSingleNodeContent("content", stripCData=True)
                name = "%s - %s" % (name, date)

                date = xmlData.GetTagAttribute("show", {"date": None})
                day, month, year = date.split("-")
                time = xmlData.GetTagAttribute("show", {"time": None})
                hours, minutes = time.split(":")

                episodeItem = mediaitem.MediaItem(name, None)
                episodeItem.type = 'video'
                episodeItem.thumb = thumb
                episodeItem.description = description
                episodeItem.icon = self.icon
                episodeItem.SetDate(year, month, day, hours, minutes, 0)
                episodeItem.complete = True
                showItem.items.append(episodeItem)

                part = episodeItem.CreateNewEmptyMediaPart()
                part.AppendMediaStream(url, 1225)
                # we guess the other streams
                part.AppendMediaStream(url.replace("/middel/", "/hoog/"), 1825)
                part.AppendMediaStream(url.replace("/middel/", "/laag/"), 630)

        return data, items

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

        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)
        item.complete = True
        return item
