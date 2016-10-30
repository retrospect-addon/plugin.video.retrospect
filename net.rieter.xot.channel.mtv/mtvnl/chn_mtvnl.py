import mediaitem
#import contextmenu
import chn_class

from logger import Logger
from urihandler import UriHandler
from regexer import Regexer
from helpers.htmlentityhelper import HtmlEntityHelper


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
        self.noImage = "mtvnlimage.png"

        # setup the urls
        if self.channelCode == "mtvnl":
            self.mainListUri = "http://api.mtvnn.com/v2/site/m79obhheh2/nl/franchises.json?per=2147483647"
            self.baseUrl = "http://www.mtv.nl"

        elif self.channelCode == "mtvde":
            self.mainListUri = "http://api.mtvnn.com/v2/site/va7rcfymx4/de/franchises.json?per=2147483647"
            self.baseUrl = "http://www.mtv.de"

        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.1.8.1.swf"

        # setup the main parsing data
        if "json" in self.mainListUri:
            Logger.Debug("Doing a JSON version of MTV")
            self.episodeItemJson = ()
            # self.videoItemRegex = '("original_title"[\w\W]+?\}\}(?:,\{|]))'
            self.videoItemJson = ()
            self.CreateEpisodeItem = self.CreateEpisodeItemJson
            self.CreateVideoItem = self.CreateVideoItemJson
        else:
            Logger.Debug("Doing a HTML version of MTV")
            self.episodeItemRegex = '<a href="/(shows/[^"]+)" title="([^"]+)"><img [^>]+src="([^"]+)"'  # used for the ParseMainList
            self.videoItemRegex = '<a href="([^"]+)" title="([^"]+)">(?:<span class=\Wepisode_number\W>(\d+)</span>){0,1}[\w\W]{0,100}?<img[^>]+src="([^"]+)"[^>]+\W+</a>'
            self.folderItemRegex = '<li>\W+<a href="/(seizoen/[^"]+)">([^<]+)</a>'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        # http://www.mtv.nl/shows/195-16-pregnant
        url = "%s/%s" % (self.baseUrl, resultSet[0])
        item = mediaitem.MediaItem(resultSet[1], url)
        item.icon = self.icon
        item.thumb = resultSet[2]
        item.complete = True
        return item

    def CreateEpisodeItemJson(self, resultSet):
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

        Logger.Trace(resultSet)

        # add  { to make it valid Json again. if it would be in the regex it would
        # not find all items
        # data = JsonHelper("{%s" % (resultSet,))

        # title
        localTitle = resultSet.get("local_title")
        originalTitle = resultSet.get("original_name")
        if localTitle == "" or localTitle is None:
            title = originalTitle
        elif originalTitle != localTitle:
            title = "%s (%s)" % (localTitle, originalTitle)
        else:
            title = localTitle

        # the URL
        serieId = resultSet["id"]
        url = "%sepisodes.json?per=2147483647&franchise_id=%s" % (self.mainListUri[0:43], serieId)
        
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.complete = True

        # thumbs
        if "image" in resultSet and resultSet["image"] is not None:
            thumb = resultSet["image"]["riptide_image_id"]
            thumb = "http://images.mtvnn.com/%s/original" % (thumb,)
            item.thumb = thumb

        # others
        item.description = resultSet["local_long_description"]

        # http://www.mtv.nl/shows/195-16-pregnant
        return item

    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.
        
        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex
        
        Returns:
        A new MediaItem of type 'folder'
        
        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes 
        and are specific to the channel.
         
        """
        
        name = resultSet[1].capitalize()
        item = mediaitem.MediaItem(name, "%s/%s" % (self.baseUrl, resultSet[0]))
        item.icon = self.icon
        item.type = 'folder'
        item.complete = True
        return item

    def CreateVideoItem(self, resultSet):
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

        url = resultSet[0]
        title = resultSet[1]
        part = resultSet[2]

        # retrieve the Full quality thumb
        thumb = resultSet[3]
        thumb = "%s/original" % (thumb[:thumb.rfind("/")],)

        if not (part == ""):
            title = "%s - %s" % (part, title)

        item = mediaitem.MediaItem(title, url)
        item.thumb = thumb
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        return item

    def CreateVideoItemJson(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.UpdateVideoItem method is called if the item is focussed or selected
        for playback.

        """

        Logger.Trace(resultSet)

        # get the title
        originalTitle = resultSet.get("original_title")
        localTitle = resultSet.get("local_title")
        #Logger.Trace("%s - %s", originalTitle, localTitle)
        if originalTitle == "":
            title = localTitle
        else:
            title = originalTitle

        # get the other meta data
        playLists = resultSet.get("local_playlists", [])
        videoMgid = None
        for playList in playLists:
            language = playList["language_code"]
            if language == self.language:
                Logger.Trace("Found '%s' playlist, using this one.", language)
                videoMgid = playList["id"]
                break
            elif language == "en":
                Logger.Trace("Found '%s' instead of '%s' playlist", language, self.language)
                videoMgid = playList["id"]

        if videoMgid is None:
            Logger.Error("No video MGID found for: %s", title)
            return None

        url = "http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:local_playlist-%s" % (videoMgid,)

        thumb = resultSet.get("riptide_image_id")
        thumb = "http://images.mtvnn.com/%s/original" % (thumb,)

        description = resultSet.get("local_long_description")

        date = resultSet.get("published_from")
        date = date[0:10].split("-")

        item = mediaitem.MediaItem(title, url)
        item.thumb = thumb
        item.description = description
        item.icon = self.icon
        item.type = 'video'
        item.SetDate(date[0], date[1], date[2])
        item.complete = False
        return item

    def UpdateVideoItem(self, item):
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

        url = item.url
        data = UriHandler.Open(url)

        if "json" in self.mainListUri:
            metaData = data
        else:
            mgid = Regexer.DoRegex("mgid:[^ ]+playlist-[abcdef0-9]+", data)[0]
            mgidUrlEncoded = HtmlEntityHelper.UrlEncode(mgid)
            metaData = UriHandler.Open("http://api.mtvnn.com/v2/mrss.xml?uri=%s" % (mgidUrlEncoded,))

        videoUrl = Regexer.DoRegex("<media:content[^>]+url='([^']+)'>", metaData)[0]
        Logger.Trace(videoUrl)
        videoData = UriHandler.Open(videoUrl)
        videoItems = Regexer.DoRegex('<rendition[^>]+bitrate="(\d+)"[^>]*>\W+<src>([^<]+)<', videoData)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        for videoItem in videoItems:
            mediaUrl = self.GetVerifiableVideoUrl(videoItem[1])
            part.AppendMediaStream(mediaUrl, videoItem[0])

        item.complete = True
        return item
