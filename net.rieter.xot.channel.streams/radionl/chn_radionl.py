#===============================================================================
# Import the default modules
#===============================================================================
import os

#===============================================================================
# Make global object available
#===============================================================================
import mediaitem
import chn_class

from logger import Logger
from urihandler import UriHandler
from helpers.ziphelper import ZipHelper
from xbmcwrapper import XbmcDialogProgressWrapper


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

        self.mainListUri = "#mainlist"
        self._add_data_parser(url="#mainlist", preprocessor=self.ParseRadioList)
        self._add_data_parser(url="*", preprocessor=self.ParseSubList)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "radionlimage.png"

        #===============================================================================================================
        # non standard items

        # download the stream data
        dataPath = os.path.join(self.path, "data")
        Logger.debug("Checking '%s' for data", dataPath)
        if not os.path.isdir(dataPath):
            Logger.info("No data found at '%s', downloading stream data", dataPath)
            url = "http://www.rieter.net/net.rieter.xot.repository/net.rieter.xot.channel.streams/" \
                  "net.rieter.xot.channel.streams.radionl.data.zip"

            # give the user feedback
            progressDialog = XbmcDialogProgressWrapper("Downloading Data",
                                                       "net.rieter.xot.channel.streams.radionl.data.zip", url)

            # download the zipfile
            zipFile = UriHandler.download(url, "net.rieter.xot.channel.streams.radionl.data.zip",
                                          self.get_default_cache_path(), progressDialog)

            # and unzip it
            ZipHelper.unzip(zipFile, dataPath)

            if os.path.isdir(dataPath):
                Logger.info("Data successfully downloaded to: %s", dataPath)

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
      
    def ParseRadioList(self, data):
        """Parses the mainlist of the channel and returns a list of MediaItems

        This method creates a list of MediaItems that represent all the different
        programs that are available in the online source. The list is used to fill
        the ProgWindow.

        Keyword parameters:
        returnData : [opt] boolean - If set to true, it will return the retrieved
                                     data as well

        Returns a list of MediaItems that were retrieved.

        """

        items = []

        # read the regional ones
        # noinspection PyUnresolvedReferences
        dataPath = os.path.abspath(os.path.join(__file__, '..', 'data'))
        Logger.info("Radio stations located at: %s", dataPath)
        regionals = os.listdir(os.path.join(dataPath, "Regionale Omroepen"))
        for regional in regionals:
            path = os.path.join(dataPath, "Regionale Omroepen", regional) 
            if not os.path.isdir(path):
                continue
            item = mediaitem.MediaItem(regional, path)
            item.complete = True
            items.append(item)
            pass

        # add the National ones
        item = mediaitem.MediaItem("Nationale Radiozenders", os.path.join(dataPath))
        item.complete = True
        items.insert(0, item)

        item = mediaitem.MediaItem("Webradio", os.path.join(dataPath, "Webradio"))
        item.complete = True
        items.insert(0, item)
        return data, items
    
    def ParseSubList(self, data):
        """Process the selected item and get's it's child items.

        Arguments:
        item : [opt] MediaItem - the selected item

        Returns:
        A list of MediaItems that form the childeren of the <item>.

        Accepts an <item> and returns a list of MediaListems with at least name & url
        set. The following actions are done:

        * loading of the data from the item.url
        * perform pre-processing actions
        * creates a sorted list folder items using self.folderItemRegex and self.create_folder_item
        * creates a sorted list of media items using self.videoItemRegex and self.create_video_item
        * create page items using self.ProcessPageNavigation

        if item = None then an empty list is returned.

        """

        item = self.parentItem
        url = item.url
        items = []
        
        stations = os.listdir(url)
        for station in stations:
            if not station.endswith(".strm"):
                continue
            
            name = station.replace(".strm", "")
            stream = os.path.join(url, station)
            stationItem = mediaitem.MediaItem(name, stream)
            stationItem.icon = os.path.join(url, "%s%s" % (name, ".tbn"))
            stationItem.complete = True
            stationItem.description = stationItem.name
            stationItem.append_single_stream(stream)
            stationItem.type = "playlist"
            stationItem.thumb = stationItem.icon
            items.append(stationItem)
            pass
        
        return data, items
