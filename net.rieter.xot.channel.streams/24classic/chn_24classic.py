import mediaitem
import chn_class

from logger import Logger
from helpers.jsonhelper import JsonHelper
from urihandler import UriHandler
from parserdata import ParserData


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
        self.noImage = ""

        # setup the urls
        self.noImage = "24classicsimage.png"
        self.mainListUri = "http://www.24classics.com/app/core/server_load.php?r=default&page=luister&serial=&subserial=&hook="
        self.baseUrl = "http://www.24classics.com"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              json=True, preprocessor=self.MakeEpisodeDictionaryArray,
                              parser=["items", ], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["items", "tracklist"], creator=self.CreateMusicItem,
                              updater=self.UpdateMusicItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def MakeEpisodeDictionaryArray(self, data):
        """Performs pre-process actions for data processing and converts the strange dictionary
        with numbered keys into a proper dictionary.

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.

        """

        Logger.info("Performing Pre-Processing")
        items = []
        jsonData = JsonHelper(data)
        dictItems = jsonData.get_value("items", fallback=[])
        for item in dictItems:
            if item == "banners" or item == "curators":
                continue
            items.append(self.create_episode_item(dictItems[item]))

        Logger.debug("Pre-Processing finished")
        data = ""
        return data, items

    def create_episode_item(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)
        title = resultSet["title"]
        description = resultSet.get("description", "")
        descriptionNL = resultSet.get("introduction_lan1", "")
        thumb = resultSet["image_full"]
        url = "http://www.24classics.com/app/core/server_load.php?r=default&page=luister&serial=&subserial=&hook=%(hook)s" % resultSet

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.thumb = thumb
        item.description = "%s\n\n%s" % (descriptionNL, description)
        item.description = item.description.strip()
        item.complete = True
        return item

    def CreateMusicItem(self, resultSet):
        """Creates a MediaItem of type 'audio' using the resultSet from the regex.

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

        Logger.trace(resultSet)
        title = "%(composers)s - %(title)s" % resultSet
        url = "http://www.24classics.com/app/ajax/auth.php?serial=%(serial)s" % resultSet

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = "video"
        # item.type = "audio"  # seems to not really work well with track numbers (not showing)
        item.thumb = self.parentItem.thumb
        item.complete = False
        item.description = "Composers: %(composers)s\nPerformers: %(performers)s" % resultSet
        item.set_info_label("TrackNumber", resultSet["order"])
        item.set_info_label("AlbumArtist", resultSet["composers"].split(","))
        item.set_info_label("Artist", resultSet["performers"].split(","))
        return item

    def UpdateMusicItem(self, item):
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

        Logger.debug('Starting UpdateMusicItem for %s (%s)', item.name, self.channelName)
        url, data = item.url.split("?")

        data = UriHandler.open(url, proxy=self.proxy, params=data, additional_headers=item.HttpHeaders)
        Logger.trace(data)
        jsonData = JsonHelper(data)
        url = jsonData.get_value("url", fallback=None)

        if url:
            item.append_single_stream(url)
            item.Complete = True
        return item
