# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.mediaitem import MediaItem


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

        self.mainListUri = "https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/browse?" \
                           "lang=nl&" \
                           "features=watch-web-redesign%2CimageRatio58x13%2CpromoTiles%2CopenAuthz&" \
                           "headerBgImageWidth=1280&countryCode=NL&tz=UTC+0100"
        self._add_data_parser(self.mainListUri, name="MainList Parsers", json=True,
                              parser=["page", "buckets"], creator=self.create_bucket)

        self._add_data_parser("#bucket", name="Bucket Sublist", json=True,
                              parser=[], creator=self.create_sub_bucket,
                              preprocessor=self.extract_sub_bucket)

        # Other URLs
        # self.mainListUri = "https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/bucket?" \
        #                    "lang=nl&features=watch-web-redesign%2CimageRatio58x13%2CpromoTiles%2CopenAuthz&" \
        #                    "bucketId=39623&headerBgImageWidth=1280&countryCode=NL&tz=UTC+0100"
        #
        # self._add_data_parser("https://watch-cdn.product.api.espn.com/api/product/v3/watchespn/web/bucket?",
        #                       name="ESPN mainlist categories", json=True,
        #                       parser=[], creator=self.create_episode_item)

    def create_bucket(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = MediaItem(result_set["name"], "#bucket")
        item.description = result_set.get("description")
        item.metaData["bucket"] = result_set["contents"]
        return item

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
        item = MediaItem(title, url)
        item.thumb = result_set["imageHref"]

        return item

