import datetime

import chn_class
from logger import Logger
from mediaitem import MediaItem


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
        self.noImage = "vtmbeimage.jpg"

        # setup the urls
        self.mainListUri = "http://vtm.be/feed/programs?format=json&type=all&only_with_video=true"
        self.baseUrl = "http://vtm.be"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, json=True,
                            creator=self.CreateEpisodeItem, parser=("response", "items"))

        self._AddDataParser("http://vtm.be/feed/articles?program=", json=True,
                            creator=self.CreateVideoItem, parser=("response", "items"))

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

               Arguments:
               resultSet : list[string] - the resultSet of the self.episodeItemRegex

               Returns:
               A new MediaItem of type 'folder'

               This method creates a new MediaItem from the Regular Expression or Json
               results <resultSet>. The method should be implemented by derived classes
               and are specific to the channel.

               """

        Logger.Trace(resultSet)

        title = resultSet['title']
        archived = resultSet['archived']
        if archived:
            Logger.Warning("Found archived item: %s", title)
            return None

        programId = resultSet['id']
        url = "http://vtm.be/feed/articles?program=%s&fields=text,video&type=all&sort=mostRecent&&count=100&filterExcluded=true" % (programId, )
        item = MediaItem(title, url)
        item.fanart = self.fanart
        item.thumb = self.noImage
        item.description = resultSet.get('body', None)

        if 'images' in resultSet and 'image' in resultSet['images']:
            item.thumb = resultSet['images']['image'].get('full', self.noImage)
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

        Logger.Trace(resultSet)

        title = resultSet['title']
        item = MediaItem(title, "", type="video")
        item.description = resultSet.get('text')

        if 'image' in resultSet:
            item.thumb = resultSet['image'].get("full", None)

        created = Channel.GetDateFromPosix(resultSet['created']['timestamp'])
        item.SetDate(created.year, created.month, created.day, created.hour, created.minute, created.second)

        if 'video' not in resultSet:
            Logger.Warning("Found item without video: %s", item)
            return None

        item.AppendSingleStream(resultSet['video']['url']['default'], 0)
        item.complete = True
        return item

    @staticmethod
    def GetDateFromPosix(posix, tz=None):
        # type: (float) -> datetime.datetime
        """ Creates a datetime from a Posix Time stamp

        @param posix:   the posix time stamp integer
        @return:        a valid datetime.datetime object.
        """

        return datetime.datetime.fromtimestamp(posix, tz)
