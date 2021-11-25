# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData

from resources.lib import chn_class, contenttype
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


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
        self.noImage = "channel9image.png"

        # setup the urls
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://docs.microsoft.com"

        # setup the main parsing data
        main_list_regex = r'<li>\W+<a href="([^"]+Browse[^"]+)">(\D[^<]+)</a>'  # used for the ParseMainList
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.fetch_pages,
                              parser=[], creator=self.create_episode_item)

        # folder_regex = r'<a[^>]+href="(?<url>[^"]+)"[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)"[^>]*alt="(?<title>[^"]+)"[^>]*>\W*(?:<div[^>]*>\W*<time[^>]+datetime="(?<date>[^"]+)"[^>]*>[^>]+>\W*</div>)?\W*</a>\W*</article'
        # folder_regex = Regexer.from_expresso(folder_regex)
        # self._add_data_parser("*", parser=folder_regex, creator=self.create_folder_item)
        #
        # page_regex = r'<a href="([^"]+page=)(\d+)"'
        # page_regex = Regexer.from_expresso(page_regex)
        # self.pageNavigationRegexIndex = 1
        # self._add_data_parser("*", parser=page_regex, creator=self.create_page_item)
        #
        # video_regex = r'<a[^>]+href="(?<url>[^"]+)"[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)"[^>]*alt="(?<title>[^"]+)"[^>]*>\W*<tim'
        # video_regex = Regexer.from_expresso(video_regex)
        # self._add_data_parser("*", parser=video_regex, creator=self.create_video_item,
        #                       updater=self.update_video_item)

        # =========================== Actual channel setup STOPS here ==============================
        return

    def fetch_pages(self, combined_data):
        """ Fetches the pages for the mainlist

        :param str combined_data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        combined_data = []
        max_items = 31
        skip = 30
        i = 0

        while i < max_items:
            url = "https://docs.microsoft.com/api/contentbrowser/search/shows?" \
                  "locale=en-us&" \
                  "facet=products&" \
                  "facet=type&" \
                  "%24orderBy=latest_episode_upload_at%20desc&" \
                  "%24skip={:d}&" \
                  "%24top=30".format(i)
            raw_data = UriHandler.open(url)
            json_data = JsonHelper(raw_data)
            combined_data += json_data.get_value("results", fallback=[])
            max_items = json_data.get_value("count")
            i += skip

        data = JsonHelper("[]")
        data.json = combined_data

        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        hidden = result_set["hidden"]
        if hidden:
            return None

        name = result_set["title"]
        # item_type = result_set["type"]
        # item_id = result_set["uid"]
        slug = result_set["url"]
        # https://docs.microsoft.com/api/hierarchy/shows/xamarinshow/episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc
        url = "{}/api/hierarchy{}episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc".format(self.baseUrl, slug)

        item = FolderItem(name, url, content_type=contenttype.EPISODES)

        thumb = result_set["image_url"]
        if thumb:
            # https://docs.microsoft.com/shows/vs-code-livestreams/media/vscodelivestream_383x215.png
            thumb = "{}{}{}".format(self.baseUrl, slug, thumb)
            item.thumb = thumb

        # '2021-11-23T22:16:00Z'
        latest = result_set.get("latest_episode_upload_at")
        if latest:
            latest = latest.rsplit(".", 1)[0]
            latest = latest.replace("Z", "")
            time_stamp = DateHelper.get_date_from_string(latest, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])
        return item

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = chn_class.Channel.create_folder_item(self, result_set)
        if not item:
            return item

        if "date" not in result_set or not result_set["date"]:
            return item

        data_time = result_set["date"]
        date_str = data_time.split(" ")[0]
        time_stamp = DateHelper.get_date_from_string(date_str, "%Y-%m-%d")
        item.set_date(*time_stamp[0:6])
        return item

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url)

        urls = Regexer.do_regex(r'<a[^"]+href="([^"]+.(?:wmv|mp4))"[^>]*>\W*(High|Medium|Mid|Low|MP4)', data)
        for url in urls:
            if url[1].lower() == "high":
                bitrate = 2000
            elif url[1].lower() == "medium" or url[1].lower() == "mid":
                bitrate = 1200
            elif url[1].lower() == "low" or url[1].lower() == "mp4":
                bitrate = 200
            else:
                bitrate = 0
            item.add_stream(HtmlEntityHelper.convert_html_entities(url[0]), bitrate)

        item.complete = True
        return item
