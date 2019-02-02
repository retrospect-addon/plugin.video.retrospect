#===============================================================================
# Import the default modules
#===============================================================================
import os

#===============================================================================
# Make global object available
#===============================================================================
import chn_class
from mediaitem import MediaItem
from logger import Logger


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "tvnlimage.png"

        self.mainListUri = "#mainlist"
        self._add_data_parser(url="#mainlist", preprocessor=self.parse_tv_list)
        self._add_data_parser(url="*", preprocessor=self.parse_sub_list)

        #============================= Actual channel setup STOPS here =============================
        return

    def parse_tv_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        # read the regional ones
        # noinspection PyUnresolvedReferences
        data_path = os.path.abspath(os.path.join(__file__, '..', 'data'))
        Logger.info("TV streams located at: %s", data_path)
        regionals = os.listdir(data_path)
        Logger.trace(regionals)
        for regional in regionals:
            path = os.path.join(data_path, regional)
            if not os.path.isdir(path):
                continue
            item = MediaItem(regional, path)
            item.complete = True
            items.append(item)

        # add the National ones
        self.mainListItems = items
        return data, items

    def parse_sub_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        item = self.parentItem
        Logger.debug("trying first items")
        url = item.url
        items = []

        stations = os.listdir(url)
        for station in stations:
            if not station.endswith(".m3u"):
                continue

            name = station.replace(".m3u", "")
            stream = os.path.join(url, station)
            station_item = MediaItem(name, stream)
            station_item.icon = os.path.join(url, "%s%s" % (name, ".tbn"))
            station_item.complete = True
            station_item.description = station_item.name
            station_item.append_single_stream(stream)
            station_item.type = "playlist"
            station_item.thumb = station_item.icon
            items.append(station_item)

        return data, items
