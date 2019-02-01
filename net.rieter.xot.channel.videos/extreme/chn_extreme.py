import chn_class

from mediaitem import MediaItem
from streams.smil import Smil
from regexer import Regexer
from logger import Logger
from streams.youtube import YouTube
from urihandler import UriHandler
from streams.brightcove import BrightCove


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
        self.noImage = "extremeimage.png"

        # setup the urls
        self.mainListUri = "http://extreme.com/"
        self.baseUrl = "http://extreme.com"

        # setup the main parsing data
        self.episodeItemRegex = '<li><a href="([^"]+)" title=[^>]*>([^<]+)</a></li>'
        self.videoItemRegex = r'<img src="(?P<thumburl>[^"]+)"[^>]*alt="([^"]+)" /></a>[\w\W]' \
                              r'{0,200}<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^"]+)</a></p>' \
                              r'<p class="description">(?P<description>[^"]+)</p>'
        self.mediaUrlRegex = r'fo.addVariable\("id", "([^"]+)"\)'
        self.pageNavigationRegex = r'<a[^>]*href="(/[^"]+page=)(\d+)">\d+</a>'
        self.pageNavigationRegexIndex = 1

        # ========================== Actual channel setup STOPS here ===============================
        return
    
    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = MediaItem(result_set[1], "%s%s?page=1" % (self.baseUrl, result_set[0]))
        item.icon = self.icon
        item.complete = True
        return item

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)
        
        # get additional info
        data = UriHandler.open(item.url, proxy=self.proxy)

        #<param name="flashvars" value="id=dj0xMDEzNzQyJmM9MTAwMDAwNA&amp;tags=source%253Dfreecaster&amp;autoplay=1" />
        # http://freecaster.tv/player/smil/dj0xMDEzNzQyJmM9MTAwMDAwNA -> playlist with bitrate
        # http://freecaster.tv/player/smil/dj0xMDEzNzQyJmM9MTAwMDAwNA -> info (not needed, get description from main page.

        you_tube_url = Regexer.do_regex('"(https://www.youtube.com/embed/[^\"]+)', data)
        if you_tube_url:
            Logger.debug("Using Youtube video")
            part = item.create_new_empty_media_part()
            you_tube_url = you_tube_url[0].replace("embed/", "watch?v=")
            for s, b in YouTube.get_streams_from_you_tube(you_tube_url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
            return item

        guid = Regexer.do_regex(
            r'<meta property="og:video" content="http://player.extreme.com/FCPlayer.swf\?id=([^&]+)&amp[^"]+" />',
            data)
        if len(guid) > 0:
            url = '%s/player/smil/%s' % (self.baseUrl, guid[0],) 
            data = UriHandler.open(url)

            smiller = Smil(data)
            base_url = smiller.get_base_url()
            urls = smiller.get_videos_and_bitrates()

            part = item.create_new_empty_media_part()
            for url in urls:
                if "youtube" in url[0]:
                    for s, b in YouTube.get_streams_from_you_tube(url[0], self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                else:
                    part.append_media_stream("%s%s" % (base_url, url[0]), bitrate=int(int(url[1]) / 1000))
                item.complete = True

            Logger.trace("update_video_item complete: %s", item)
            return item

        # Try the brightcove
        bright_cove_regex = r'<object id="myExperience[\w\W]+?videoPlayer" value="(\d+)"[\w\W]{0,1000}?playerKey" value="([^"]+)'
        bright_cove_data = Regexer.do_regex(bright_cove_regex, data)
        Logger.trace(bright_cove_data)
        if len(bright_cove_data) > 0:
            seed = "c5f9ae8729f7054d43187989ef3421531ee8678d"
            object_data = bright_cove_data[0]
            player_key = str(object_data[1])
            video_id = int(object_data[0])

            part = item.create_new_empty_media_part()
            # But we need the IOS streams!
            amf_helper = BrightCove(Logger.instance(), player_key, video_id, str(item.url), seed, proxy=self.proxy)
            for stream, bitrate in amf_helper.get_stream_info(renditions="IOSRenditions"):
                part.append_media_stream(stream, bitrate)
                item.complete = True

        # Logger.Error("Cannot find GUID in url: %s", item.url)
        return item
