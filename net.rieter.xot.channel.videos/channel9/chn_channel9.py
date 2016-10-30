import urlparse

import mediaitem
#import contextmenu
import chn_class

from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.datehelper import DateHelper
from helpers.htmlhelper import HtmlHelper
from helpers.xmlhelper import XmlHelper


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
        self.noImage = "channel9image.png"

        # setup the urls
        self.mainListUri = "http://channel9.msdn.com/Browse"
        self.baseUrl = "http://channel9.msdn.com"

        # setup the main parsing data
        self.episodeItemRegex = '<li>\W+<a href="([^"]+Browse[^"]+)">(\D[^<]+)</a>'  # used for the ParseMainList
        self.videoItemRegex = '<item>([\W\w]+?)</item>'
        self.folderItemRegex = '<a href="([^"]+)" class="title">([^<]+)</a>([\w\W]{0,600})</li>'
        self.folderItemRegex = "(?:%s|%s)" % (self.folderItemRegex, '<li>\W+<a href="(/Browse[^"]+)">(\D[^<]+)')
        self.pageNavigationRegex = '<a href="([^"]+page[^"]+)">(\d+)</a>'  # self.pageNavigationIndicationRegex
        self.pageNavigationRegexIndex = 1

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        url = urlparse.urljoin(self.baseUrl, HtmlEntityHelper.ConvertHTMLEntities(resultSet[0]))
        name = resultSet[1]

        if name == "Tags":
            return None
        if name == "Authors":
            return None
        if name == "Most Viewed":
            return None
        if name == "Top Rated":
            name = "Recent"
            url = "http://channel9.msdn.com/Feeds/RSS"
        else:
            url = "%s?sort=atoz" % (url,)

        item = mediaitem.MediaItem(name, url)
        item.icon = self.icon
        item.complete = True
        return item

    def PreProcessFolderList(self, data):
        """Performs pre-process actions for data processing/

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

        Logger.Info("Performing Pre-Processing")
        items = []
        data = data.replace("&#160;", " ")

        pageNav = data.find('<div class="pageNav">')
        if pageNav > 0:
            data = data[0:pageNav]

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreatePageItem(self, resultSet):
        """Creates a MediaItem of type 'page' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex

        Returns:
        A new MediaItem of type 'page'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        url = urlparse.urljoin(self.baseUrl, HtmlEntityHelper.ConvertHTMLEntities(resultSet[0]))
        item = mediaitem.MediaItem(resultSet[self.pageNavigationRegexIndex], url)
        item.type = "page"
        item.complete = True
        item.SetDate(2022, 1, 1, text="")

        Logger.Trace("Created '%s' for url %s", item.name, item.url)
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

        if len(resultSet) > 3 and resultSet[3] != "":
            Logger.Debug("Sub category folder found.")
            url = urlparse.urljoin(self.baseUrl, HtmlEntityHelper.ConvertHTMLEntities(resultSet[3]))
            name = "\a.: %s :." % (resultSet[4],)
            item = mediaitem.MediaItem(name, url)
            item.thumb = self.noImage
            item.complete = True
            item.type = "folder"
            return item

        url = urlparse.urljoin(self.baseUrl, HtmlEntityHelper.ConvertHTMLEntities(resultSet[0]))
        name = HtmlEntityHelper.ConvertHTMLEntities(resultSet[1])

        helper = HtmlHelper(resultSet[2])
        description = helper.GetTagContent("div", {'class': 'description'})

        item = mediaitem.MediaItem(name, "%s/RSS" % (url,))
        item.thumb = self.noImage
        item.type = 'folder'
        item.description = description.strip()

        date = helper.GetTagContent("div", {'class': 'date'})
        if date == "":
            date = helper.GetTagContent("span", {'class': 'lastPublishedDate'})

        if not date == "":
            dateParts = Regexer.DoRegex("(\w+) (\d+)[^<]+, (\d+)", date)
            if len(dateParts) > 0:
                dateParts = dateParts[0]
                monthPart = dateParts[0].lower()
                dayPart = dateParts[1]
                yearPart = dateParts[2]

                try:
                    month = DateHelper.GetMonthFromName(monthPart, "en")
                    item.SetDate(yearPart, month, dayPart)
                except:
                    Logger.Error("Error matching month: %s", monthPart, exc_info=True)

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

        # Logger.Trace(resultSet)

        xmlData = XmlHelper(resultSet)
        title = xmlData.GetSingleNodeContent("title")
        url = xmlData.GetSingleNodeContent("link")
        description = xmlData.GetSingleNodeContent("description")
        description = description.replace("<![CDATA[ ", "").replace("]]>", "").replace("<p>", "").replace("</p>", "\n")

        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.complete = False
        item.description = description
        item.thumb = self.noImage
        item.icon = self.icon

        date = xmlData.GetSingleNodeContent("pubDate")
        dateResult = Regexer.DoRegex("\w+, (\d+) (\w+) (\d+)", date)[-1]
        day = dateResult[0]
        monthPart = dateResult[1].lower()
        year = dateResult[2]

        try:
            monthLookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            month = monthLookup.index(monthPart) + 1
            item.SetDate(year, month, day)
        except:
            Logger.Error("Error matching month: %s", resultSet[4].lower(), exc_info=True)

        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(item.url)

        urls = Regexer.DoRegex('<a href="([^"]+.(?:wmv|mp4))">(High|Medium|Mid|Low|MP4)', data)
        mediaPart = mediaitem.MediaItemPart(item.name)
        for url in urls:
            if url[1].lower() == "high":
                bitrate = 2000
            elif url[1].lower() == "medium" or url[1].lower() == "mid":
                bitrate = 1200
            elif url[1].lower() == "low" or url[1].lower() == "mp4":
                bitrate = 200
            else:
                bitrate = 0
            mediaPart.AppendMediaStream(HtmlEntityHelper.ConvertHTMLEntities(url[0]), bitrate)

        item.MediaItemParts.append(mediaPart)

        #images = Regexer.DoRegex('<link type="image/jpeg" rel="videothumbnail" href="([^"]+)"/>', data)
        #for image in images:
        #    thumbUrl = htmlentityhelper.HtmlEntityHelper.ConvertHTMLEntities(image)
        #    break

        item.complete = True
        return item
