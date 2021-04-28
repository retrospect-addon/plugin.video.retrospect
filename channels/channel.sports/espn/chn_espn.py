# SPDX-License-Identifier: GPL-3.0-or-later

import pytz

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    # TODO: Most of this is paid.
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        self.mainListUri = "https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/browse?" \
                           "lang=nl&" \
                           "features=watch-web-redesign%2CimageRatio58x13%2CpromoTiles%2CopenAuthz&" \
                           "headerBgImageWidth=1280&countryCode=NL&tz=UTC+0100"
        self._add_data_parser(self.mainListUri, name="MainList Parsers", json=True,
                              parser=["page", "buckets"], creator=self.create_bucket)

        self._add_data_parser("#bucket", name="Bucket Sublist", json=True,
                              parser=[], creator=self.create_sub_bucket,
                              preprocessor=self.extract_sub_bucket)

        self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/catalog/",
                              name="Bucket Catalog Parer", json=True,
                          parser=["page", "buckets"], creator=self.create_bucket_folder)

        self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/bucket",
                              name="Bucket Video Parser", json=True,
                              parser=["page", "buckets", 0, "contents"], creator=self.create_video_item)

        self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/series/",
                              name="Series parsers", json=True,
                              parser=['page', 'buckets', ('name', 'VOD', 0), "contents"],
                              creator=self.create_video_item)

        self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/playback/",
                              updater=self.update_video_item)

        # Other URLs
        # self.mainListUri = "https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/bucket?" \
        #                    "lang=nl&features=watch-web-redesign%2CimageRatio58x13%2CpromoTiles%2CopenAuthz&" \
        #                    "bucketId=39623&headerBgImageWidth=1280&countryCode=NL&tz=UTC+0100"
        #
        # self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/bucket?",
        #                       name="ESPN mainlist categories", json=True,
        #                       parser=[], creator=self.create_episode_item)

        if self.channelCode == "espnnl":
            self.__timezone = pytz.timezone("Europe/Amsterdam")
        else:
            self.__timezone = pytz.timezone("UTC")

    def create_bucket(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = FolderItem(result_set["name"], "#bucket", content_type=contenttype.TVSHOWS)
        item.description = result_set.get("description")
        item.metaData["bucket"] = result_set["contents"]
        return item

    # noinspection PyUnusedLocal
    def extract_sub_bucket(self, data):
        """ Extracts the sub buckets from a parent bucket.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        json = JsonHelper("{}")
        json.json = self.parentItem.metaData["bucket"]

        return json, []

    def create_sub_bucket(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str|dict] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["name"]
        url = result_set["links"]["self"]
        item = FolderItem(title, url, content_type=contenttype.EPISODES, media_type=mediatype.TVSHOW)
        item.thumb = result_set["imageHref"]

        return item

    def create_bucket_folder(self, result_set):
        """ Creates a MediaItem of type 'folder' for all the folders of a (sub)bucket.

        :param dict[str,dict|str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        if not result_set["links"]:
            return None
        url = result_set["links"]["self"]
        item = MediaItem(result_set["name"], url)
        item.description = result_set.get("description")
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set["name"]
        subtitle = result_set.get("subtitle")
        url = result_set["streams"][0]["links"]["play"]

        item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.type = "video"
        item.thumb = result_set.get("imageHref")
        item.description = result_set.get("description")
        if "playback/video" not in url:
            item.isPaid = True

        duration = result_set["streams"][0]["duration"].split(":")
        secs = int(duration[-1])
        minutes = int(duration[-2])
        hours = int(duration[-3]) if len(duration) > 2 else 0
        item.set_info_label("duration", 3600 * hours + 60 * minutes + secs)

        if "utc" in result_set:
            # 2021-01-25T12:00:00-05:00
            broadcast_time = result_set["utc"][:-6]
            time_stamp = DateHelper.get_date_from_string(
                broadcast_time,
                date_format="%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])
        elif subtitle:
            # TODO: convert the subtitle into a date?
            title = "{} -{}".format(title, subtitle)
            item.name = title
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

        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)

        stream = json_data.get_value("playbackState", "videoHref")
        part = item.create_new_empty_media_part()
        M3u8.update_part_with_m3u8_streams(part, stream)
        return item
