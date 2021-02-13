# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.m3u8 import M3u8
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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============

        if self.channelCode == "ketnet":
            self.noImage = "ketnetimage.jpg"
            self.mainListUri = self.__get_graph_url("content/ketnet/nl/kijken.model.json")
            self.baseUrl = "https://www.ketnet.be"
            self.mediaUrlRegex = r'playerConfig\W*=\W*(\{[\w\W]{0,2000}?);(?:.vamp|playerConfig)'

        else:
            raise IndexError("Unknow channel code {}".format(self.channelCode))

        self._add_data_parser(
            self.mainListUri, json=True, name="MainList Parser for GraphQL",
            parser=["data", "page", "pagecontent",
                    ("id", "/content/ketnet/nl/kijken/jcr:content/root/swimlane_64598007"),
                    "items"], creator=self.create_typed_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_typed_item(self, result_set):
        """ Creates a new MediaItem for a typed item.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        type_id = result_set["__typename"]
        if type_id == "Program":
            return self.create_program_item(result_set)
        else:
            Logger.warning("Unknown Graph Type: %s", type_id)

        return None

    def create_program_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        url = self.__get_graph_url(result_set["id"])
        item = MediaItem(result_set["title"], url)
        item.poster = result_set["imageUrl"]
        item.thumb = result_set["logoUrl"]
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
        if item.url.startswith("http"):
            data = UriHandler.open(item.url)
            json_data = Regexer.do_regex(self.mediaUrlRegex, data)

            json = JsonHelper(json_data[0])
            mzid = json.get_value("mzid")
            if not mzid:
                item.url = json.get_value("source", "hls")
                return self.__update_from_source(item)
        else:
            mzid = item.url

        hls_over_dash = self._get_setting("hls_over_dash", 'false') == 'true'

        from resources.lib.streams.vualto import Vualto
        v = Vualto(self, "ketnet@prod")
        item = v.get_stream_info(item, mzid, hls_over_dash=hls_over_dash)
        return item

    def __update_from_source(self, item):
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

        if not item.url.endswith("m3u8"):
            data = UriHandler.open(item.url)
            json_data = Regexer.do_regex(self.mediaUrlRegex, data)
            if not json_data:
                Logger.error("Cannot find JSON stream info.")
                return item

            json = JsonHelper(json_data[0])
            Logger.trace(json.json)
            stream = json.get_value("source", "hls")
            if stream is None:
                stream = json.get_value("mzsource", "hls")
            Logger.debug("Found HLS: %s", stream)
        else:
            stream = item.url

        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(stream):
            item.complete = True
            part.append_media_stream(s, b)

        # var playerConfig = {"id":"mediaplayer","width":"100%","height":"100%","autostart":"false","image":"http:\/\/www.ketnet.be\/sites\/default\/files\/thumb_5667ea22632bc.jpg","brand":"ketnet","source":{"hls":"http:\/\/vod.stream.vrt.be\/ketnet\/_definst_\/mp4:ketnet\/2015\/12\/Ben_ik_familie_van_R001_A0023_20151208_143112_864.mp4\/playlist.m3u8"},"analytics":{"type_stream":"vod","playlist":"Ben ik familie van?","program":"Ben ik familie van?","episode":"Ben ik familie van?: Warre - Aflevering 3","parts":"1","whatson":"270157835527"},"title":"Ben ik familie van?: Warre - Aflevering 3","description":"Ben ik familie van?: Warre - Aflevering 3"}
        return item

    def __get_graph_url(self, id):
        graph_query = "query GetPage($id: String!) { page(id: $id) { ... on Program { pageType ...program __typename } ... on Video { pageType ...video __typename } ... on Pagecontent { pageType ...pagecontent __typename } __typename } }  fragment program on Program { id title header { ...header __typename } activeTab tabs { name title type playlists { ...seasonOverviewTabItem __typename } pagecontent { ...pagecontentItem __typename } __typename } __typename }  fragment seasonOverviewTabItem on Playlist { name title type imageUrl items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } description __typename } __typename }  fragment video on Video { id videoType titleVideodetail subtitleVideodetail scaledPoster { ...scaledImage __typename } description availableUntilDate publicationDate duration episodeNr vrtPlayer { ...vrtPlayerFragment __typename } suggestions { id titleSuggestion subtitleSuggestion scaledPoster { ...scaledImage __typename } __typename } playlists { name title items { id titlePlaylist subtitlePlaylist scaledPoster { ...scaledImage __typename } description __typename } __typename } activePlaylist trackingData { programName seasonName episodeName episodeNr episodeBroadcastDate __typename } __typename }  fragment pagecontent on Pagecontent { pagecontent { ...pagecontentItem __typename } __typename }  fragment pagecontentItem on PagecontentItem { ... on Header { ...header __typename } ... on Highlight { ...highlight __typename } ... on Swimlane { ...swimlane __typename } __typename }  fragment highlight on Highlight { type title description link linkItem { ... on Game { id __typename } ... on Program { id __typename } ... on Story { id __typename } ... on Theme { id __typename } ... on Video { id __typename } __typename } buttonText imageUrl size __typename }  fragment swimlane on Swimlane { id type title style items { ... on Video { ...swimlaneVideo __typename } ... on Program { ...swimlaneProgram __typename } __typename } __typename }  fragment swimlaneVideo on Video { id type title imageUrl titleSwimlane subtitleSwimlane duration __typename }  fragment swimlaneProgram on Program { id type title accentColor imageUrl logoUrl __typename }  fragment scaledImage on ScaledImage { small medium large __typename }  fragment vrtPlayerFragment on VrtPlayerConfig { mediaReference aggregatorUrl clientCode __typename }  fragment header on Header { type title description imageUrl logoUrl __typename } "
        graph_id = "{{\"id\": \"{}\"}}".format(id)
        graph_url = "https://senior-bff.ketnet.be/graphql?query={}&variables={}".format(
            HtmlEntityHelper.url_encode(graph_query),
            HtmlEntityHelper.url_encode(graph_id)
        )
        return graph_url
