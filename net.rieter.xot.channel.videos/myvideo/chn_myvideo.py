import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from helpers.htmlentityhelper import HtmlEntityHelper


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
        self.noImage = "myvideoimage.png"

        # setup the urls
        self.mainListUri = "http://www.myvideo.nl/"
        self.baseUrl = "http://www.myvideo.nl"

        # setup the main parsing data
        self.episodeItemRegex = "<a class='nArrow' href='([^']+)' title='[^']*'>([^<]+)</a>"
        self._add_data_parser(self.mainListUri, preprocessor=self.AddCategories,
                              parser=self.episodeItemRegex, creator=self.create_episode_item)

        # Add generic Pre Procesor
        self._add_data_parser("*", preprocessor=self.pre_process_folder_list)

        self.videoItemRegex = "<img id='([^']+)' src='([^']+)' class='vThumb' alt='[^']*' [^>]+></a></div></div><div class='sCenter vTitle'><span class='title'><a[^>]+title='([^']+)'"
        self.mediaUrlRegex = '<item>\W*<file>\W*([^>]*)\W*</file>\W*<bandwidth>(\d+)</bandwidth>'
        self._add_data_parser("*", parser=self.episodeItemRegex, creator=self.create_episode_item,
                              updater=self.update_video_item)

        self.pageNavigationRegex = "<a class='pView pnNumbers'  href='([^?]+\?lpage=)(\d+)([^']+)"
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=self.pageNavigationRegex, creator=self.create_page_item)

        #===============================================================================================================
        # non standard items
        self.categoryName = ""

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
    
    def AddCategories(self, data):
        """ Adds categories to the mainlist

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
        
        item = mediaitem.MediaItem("Nieuwste videos", "http://www.myvideo.nl/news.php?rubrik=rljgs")
        item.dontGroup = True
        items.append(item)
        
        item = mediaitem.MediaItem("Meest bekeken videos", "http://www.myvideo.nl/news.php?rubrik=tjyec")
        item.dontGroup = True
        items.append(item)

        item = mediaitem.MediaItem("Meest besproken videos", "http://www.myvideo.nl/news.php?rubrik=vpjpr")
        item.dontGroup = True
        items.append(item)
        
        item = mediaitem.MediaItem("Best beoordeelde videos", "http://www.myvideo.nl/news.php?rubrik=xayvg")
        item.dontGroup = True
        items.append(item)
        
        item = mediaitem.MediaItem("Favoriete videos", "http://www.myvideo.nl/news.php?rubrik=pcvbc")
        item.dontGroup = True
        items.append(item)

        return data, items
    
    def pre_process_folder_list(self, data):
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
        
        Logger.info("Performing Pre-Processing")
        items = []
        
        # extract the category name from the pagedata
        results = Regexer.do_regex("in de categorie\W+<span class='[^']+'>[^;]+;([^<]+)&quot", data)
        
        if len(results) > 0:
            self.categoryName = results[0]
        
        Logger.debug("Pre-Processing finished")
        return data, items
    
    def create_episode_item(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """
        
        #<a class='nArrow' href='([^']+)' title='[^']*'>([^<]+)</a>
        #                            0                     1                                
        item = mediaitem.MediaItem(resultSet[1], HtmlEntityHelper.strip_amp("%s%s" % (self.baseUrl, resultSet[0])))
        item.icon = self.icon
        Logger.trace("%s (%s)", item.name, item.url)
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

        Logger.trace('starting FormatVideoItem for %s', self.channelName)
        #<img id='([^']+)' src='([^']+)' class='vThumb' alt='[^']*'/></a></div></div><div class='sCenter vTitle'><span class='title'><a[^>]+title='([^']+)'>
        #            0            1                                                                                                                    2
        name = resultSet[2]
        item = mediaitem.MediaItem(name, HtmlEntityHelper.strip_amp("%s%s" % (self.baseUrl, resultSet[0])))
        
        item.description = "%s\n%s" % (self.categoryName, resultSet[2])
        item.icon = self.icon
        item.thumb = resultSet[1]
        
        # now create the video url using the 
        # http://myvideo-550.vo.llnwd.net/nl/d3/movie7/4a/thumbs/3384551_1.jpg
        # http://myvideo-550.vo.llnwd.net/nl/d3/movie7/4a/3384551.flv
        
        # het script: http://myvideo-906.vo.llnwd.net/nl/d2/movie4/d93548906.flv
        # de pagina:  http://myvideo-906.vo.llnwd.net/nl/d2/movie4/d9/3548906.flv
        
        urlResult = Regexer.do_regex("(http://myvideo[^_]+)/thumbs(/\d+)_\d+.jpg", item.thumb)
        mediaurl = ""
        if len(urlResult) > 0:
            for part in urlResult[0]:
                mediaurl = "%s%s" % (mediaurl, part)
        mediaurl = "%s.flv" % (mediaurl, )
        
        item.append_single_stream(mediaurl)
        Logger.trace("Updated mediaurl for %s", item)
        item.type = 'video'
        item.complete = True
        return item
