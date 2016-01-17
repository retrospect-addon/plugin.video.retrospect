import mediaitem
import contextmenu
import chn_class
from helpers import datehelper


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        WindowXMLDialog(self, xmlFilename, scriptPath[, defaultSkin, defaultRes]) -- Create a new WindowXMLDialog script.

        xmlFilename     : string - the name of the xml file to look for.
        scriptPath      : string - path to script. used to fallback to if the xml doesn't exist in the current skin. (eg os.getcwd())
        defaultSkin     : [opt] string - name of the folder in the skins path to look in for the xml. (default='Default')
        defaultRes      : [opt] string - default skins resolution. (default='720p')

        *Note, skin folder structure is eg(resources/skins/Default/720p)

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "gelderlandimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download Item", "CtMnDownloadItem", itemTypes="video"))

        # setup the urls
        self.mainListUri = "http://www.omroepgelderland.nl/web/Uitzending-gemist-5/TV-1/Programmas/Actuele-programmas.htm"
        self.baseUrl = "http://www.omroepgelderland.nl"
        self.swfUrl = "%s/design/channel/tv/swf/player.swf" % (self.baseUrl, )

        # setup the main parsing data
        self.episodeItemRegex = '<a href="(/web/Uitzending-gemist-5/TV-1/Programmas/Programma.htm\?p=[^"]+)"\W*>\W*' \
                                '<div[^>]+>\W+<img src="([^"]+)"[^>]+>\W+</div>\W+<div[^>]+>([^<]+)'
        self.videoItemRegex = """<div class="videouitzending[^>]+\('([^']+)','[^']+','[^']+','[^']+','([^']+) (\d+) (\w+) (\d+)','([^']+)','([^']+)'"""
        self.mediaUrlRegex = '<param\W+name="URL"\W+value="([^"]+)"'
        self.pageNavigationRegex = '(/web/Uitzending-gemist-5/TV-1/Programmas/Programma.htm\?p=Debuzz&amp;pagenr=)' \
                                   '(\d+)[^>]+><span>'
        self.pageNavigationRegexIndex = 1

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
    
    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """

        item = mediaitem.MediaItem(resultSet[2], "%s%s" % (self.baseUrl, resultSet[0]))
        item.icon = self.icon
        item.thumb = "%s%s" % (self.baseUrl, resultSet[1])
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

        #Logger.Trace(resultSet)
        
        thumbUrl = "%s%s" % (self.baseUrl, resultSet[6])
        url = "%s%s" % (self.baseUrl, resultSet[5])
        name = "%s %s %s %s" % (resultSet[1], resultSet[2], resultSet[3], resultSet[4])
        
        videoUrl = resultSet[0]
        videoUrl = videoUrl.replace(" ", "%20")
        #videoUrl = self.GetVerifiableVideoUrl(videoUrl)
        # convert RTMP to HTTP
        #rtmp://media.omroepgelderland.nl         /uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        #http://content.omroep.nl/omroepgelderland/uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        videoUrl = videoUrl.replace("rtmp://media.omroepgelderland.nl", "http://content.omroep.nl/omroepgelderland")
        
        item = mediaitem.MediaItem(name, url)
        item.thumb = thumbUrl
        item.icon = self.icon
        item.type = 'video'
        item.AppendSingleStream(videoUrl)
        
        # set date
        month = datehelper.DateHelper.GetMonthFromName(resultSet[3], "nl", False)
        day = resultSet[2]
        year = resultSet[4]
        item.SetDate(year, month, day)
        
        item.complete = True
        return item
    
    def CtMnDownloadItem(self, item):
        item = self.DownloadVideoItem(item)
        return item
