# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.helpers import datehelper


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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "omroepgelderlandimage.png"

        # setup the urls
        self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs"
        self.httpHeaders = {
            "accept": "application/vnd.groei.gelderland+json;v=1.0",
            "x-groei-layout": "wide",
            "x-groei-platform": "web"
        }
        self.baseUrl = "https://api.regiogroei.cloud"
        # https://api.regiogroei.cloud/page/program/83?slug=4daagse-journaal&origin=83

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, name="Mainlist parser", json=True,
                              parser=["components", ("type", "program-list", 0), "items"],
                              creator=self.create_episode_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return
    
    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        # https://api.regiogroei.cloud/page/program/83?slug=4daagse-journaal&origin=83
        url_info = result_set["_links"]["page"]
        url = "{}{}".format(self.baseUrl, url_info["href"])
        item = FolderItem(result_set["programTitle"], url, content_type=contenttype.EPISODES)

        synposis = result_set.get("synopsis")
        description = result_set.get("description")
        if synposis and description:
            item.description = "{}\n\n{}".format(synposis, description)
        elif synposis:
            item.description = synposis
        elif description:
            item.description = description

        # thumbnail=https://images.regiogroei.cloud/[format]/d169259e-0f0a-39b1-824d-a49f3ff7ce34.[ext]?ts=1632764016263
        item.thumb = result_set.get("thumbnail").replace("[format]", "552x310").replace("[ext]", "jpg")
        item.fanart = result_set.get("thumbnail").replace("[format]", "2456x1380").replace("[ext]", "jpg")
        # https://images.regiogroei.cloud/2456x1380/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 2456w
        # https://images.regiogroei.cloud/1104x620/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 1104w
        # https://images.regiogroei.cloud/552x310/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 552w
        # https://images.regiogroei.cloud/264x148/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 264w
        # https://images.regiogroei.cloud/112x64/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 112w

        item.complete = True
        return item
    
    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        #Logger.Trace(result_set)
        
        thumb_url = "%s%s" % (self.baseUrl, result_set[6])
        url = "%s%s" % (self.baseUrl, result_set[5])
        name = "%s %s %s %s" % (result_set[1], result_set[2], result_set[3], result_set[4])
        
        video_url = result_set[0]
        video_url = video_url.replace(" ", "%20")
        # convert RTMP to HTTP
        #rtmp://media.omroepgelderland.nl         /uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        #http://content.omroep.nl/omroepgelderland/uitzendingen/video/2012/07/120714 338 Carrie on.mp4
        video_url = video_url.replace("rtmp://media.omroepgelderland.nl",
                                      "http://content.omroep.nl/omroepgelderland")
        
        item = MediaItem(name, url, media_type=mediatype.EPISODE)
        item.thumb = thumb_url
        item.add_stream(video_url)
        
        # set date
        month = datehelper.DateHelper.get_month_from_name(result_set[3], "nl", False)
        day = result_set[2]
        year = result_set[4]
        item.set_date(year, month, day)
        
        item.complete = True
        return item
