# coding:UTF-8

import chn_class
import mediaitem
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.languagehelper import LanguageHelper
from helpers.subtitlehelper import SubtitleHelper
from parserdata import ParserData
from streams.m3u8 import M3u8
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from logger import Logger


class Channel(chn_class.Channel):
    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "nrknoimage.png"

        # setup the urls
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://psapi.nrk.no"
        # self.httpHeaders["app-version-android"] = "2500"

        #self.swfUrl = "%s/public/swf/video/svtplayer-2013.23.swf" % (self.baseUrl,)

        self._AddDataParser(self.mainListUri, preprocessor=self.CreateMainList)

        # See https://stsnapshottestwe.blob.core.windows.net/apidocumentation/documentation.html for
        # the url definitions
        self._AddDataParser("https://psapi.nrk.no/medium/tv/letters?", json=True,
                            name="Alfa Listing",
                            parser=(), creator=self.CreateAlphaItem)

        self._AddDataParser("https://psapi.nrk.no/medium/tv/letters/", json=True,
                            name="Programs from AlphaListing",
                            parser=(), creator=self.CreateEpisodeItem)

        self._AddDataParser("https://psapi.nrk.no/programs/", json=True,
                            name="Main program json video updater",
                            updater=self.UpdateJsonVideoItem)

        self._AddDataParsers(
            ("https://psapi.nrk.no/medium/tv/recommendedprograms",
             "https://psapi.nrk.no/medium/tv/popularprogramssuper",
             "https://psapi.nrk.no/medium/tv/recentlysentprograms"),
            json=True, parser=(), creator=self.CreateVideoItem)

        self._AddDataParsers(("https://psapi.nrk.no/tv/live", "https://psapi.nrk.no/radio/live"),
                             json=True, name="Live items",
                             parser=(), creator=self.CreateLiveChannelItem)
        self._AddDataParser("https://psapi.nrk.no/playback/manifest/channel/",
                            updater=self.UpdateLiveChannel)

        self._AddDataParser("https://psapi.nrk.no/medium/tv/categories", json=True,
                            name="Category listing",
                            parser=(), creator=self.CreateCategoryItem)
        self._AddDataParser("https://psapi.nrk.no/medium/tv/categories/", json=True,
                            name="Category Items",
                            parser=(), creator=self.CreateCategoryEpisodeItem)

        # The new Series/Instalments API (https://psapi-catalog-prod-we.azurewebsites.net/swagger/index.html)
        self._AddDataParser("https://psapi.nrk.no/tv/catalog/series/",
                            json=True, name="Main Series parser",
                            parser=("_links", "seasons",), creator=self.CreateInstalmentSeasonItem)

        self._AddDataParser("https://psapi.nrk.no/tv/catalog/series/[^/]+/seasons/", json=True,
                            matchType=ParserData.MatchRegex,
                            name="Videos for Serie parser - instalments",
                            parser=("_embedded", "instalments"),
                            creator=self.CreateInstalmentVideoItem)
        self._AddDataParser("https://psapi.nrk.no/tv/catalog/series/[^/]+/seasons/", json=True,
                            matchType=ParserData.MatchRegex,
                            name="Videos for Serie parser - episodes",
                            parser=("_embedded", "episodes"),
                            creator=self.CreateInstalmentVideoItem)

        # The old Series API (http://nrkpswebapi2ne.cloudapp.net/swagger/ui/index#/)
        self._AddDataParser("https://psapi.nrk.no/series/", json=True,
                            name="Main Series parser",
                            parser=("seasons",), creator=self.CreateSeriesSeasonItem)

        self._AddDataParser("https://psapi.nrk.no/series/[^/]+/seasons/", json=True,
                            matchType=ParserData.MatchRegex,
                            name="Videos for Serie parser",
                            parser=(), creator=self.CreateSeriesVideoItem)

        self._AddDataParser("*", updater=self.UpdateVideoItem)

        # ==============================================================================================================
        # non standard items
        self.__meta_data_index_category = "category_id"
        self.__api_key = "d1381d92278a47c09066460f2522a67d"

        # ==============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateMainList(self, data):
        """Performs pre-process actions for data processing

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

        live = LanguageHelper.GetLocalizedString(LanguageHelper.LiveStreamTitleId)
        live_tv = "{} - TV".format(live)
        live_radio = "{} - Radio".format(live)

        links = {
            live_tv: "https://psapi.nrk.no/tv/live?apiKey={}".format(self.__api_key),
            live_radio: "https://psapi.nrk.no/radio/live?apiKey={}".format(self.__api_key),
            "Recommended": "https://psapi.nrk.no/medium/tv/recommendedprograms?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Popular": "https://psapi.nrk.no/medium/tv/popularprogramssuper?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Recent": "https://psapi.nrk.no/medium/tv/recentlysentprograms?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Categories": "https://psapi.nrk.no/medium/tv/categories?apiKey={}".format(self.__api_key),
            "A - Å": "https://psapi.nrk.no/medium/tv/letters?apiKey={}".format(self.__api_key)
        }
        for name, url in links.iteritems():
            item = mediaitem.MediaItem(name, url)
            item.icon = self.icon
            item.thumb = self.noImage
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateAlphaItem(self, result_set):
        program_count = result_set.get("availableInternationally", 0)
        if program_count <= 0:
            return None

        title = result_set["title"]
        url_part = title.lower()
        if url_part == "0-9":
            url_part = "$"
        url = "https://psapi.nrk.no/medium/tv/letters/{}/indexelements?onlyOnDemandRights=false&" \
              "apiKey={}".format(url_part, self.__api_key)

        title = LanguageHelper.GetLocalizedString(LanguageHelper.StartWith) % (title, )
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'folder'
        item.fanart = self.fanart
        item.thumb = self.noImage
        return item

    def CreateCategoryItem(self, result_set):
        title = result_set["displayValue"]
        category_id = result_set["id"]
        url = "https://psapi.nrk.no/medium/tv/categories/{}/indexelements?apiKey={}"\
            .format(category_id, self.__api_key)
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'folder'
        item.fanart = self.fanart
        item.thumb = self.noImage
        return item

    def CreateCategoryEpisodeItem(self, result_set):
        title = result_set["title"]

        program_type = result_set.get("type", "???").lower()
        if program_type != "series":
            Logger.Debug("Item '%s' has type '%s'. Ignoring", title, program_type)
            return None

        return self.CreateGenericItem(result_set, program_type)

    def CreateEpisodeItem(self, result_set):
        title = result_set["title"]

        program_type = result_set.get("type", "???").lower()
        if program_type not in ("programme", "series"):
            Logger.Debug("Item '%s' has type '%s'. Ignoring", title, program_type)
            return None

        return self.CreateGenericItem(result_set, program_type)

    def CreateVideoItem(self, result_set):
        return self.CreateGenericItem(result_set, "programme")

    def CreateGenericItem(self, result_set, program_type):
        title = result_set["title"]

        if not result_set.get("hasOndemandRights", True):
            Logger.Debug("Item '%s' has no on-demand rights", title)
            return None

        item_id = result_set["id"]
        if program_type == "programme":
            url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(item_id, self.__api_key)
            item = mediaitem.MediaItem(title, url)
            item.type = 'video'
        else:
            use_old_series_api = False
            if use_old_series_api:
                url = "https://psapi.nrk.no/series/{}?apiKey={}".format(item_id, self.__api_key)
            else:
                url = "https://psapi.nrk.no/tv/catalog/series/{}?apiKey={}".format(item_id, self.__api_key)

            item = mediaitem.MediaItem(title, url)
            item.type = 'folder'

        item.icon = self.icon
        item.isGeoLocked = result_set.get("isGeoBlocked", result_set.get("usageRights", {}).get("isGeoBlocked", False))

        description = result_set.get("description")
        if description and description.lower() != "no description":
            item.description = description

        if "image" not in result_set or "webImages" not in result_set["image"]:
            return item

        item.thumb = self.__get_image(result_set["image"]["webImages"], "pixelWidth", "imageUrl")

        # see if there is a date?
        self.__set_date(result_set, item)
        return item

    def CreateSeriesSeasonItem(self, result_set):
        title = "Sesong {}".format(result_set["name"])
        season_id = result_set["id"]
        if not result_set.get("hasOnDemandRightsEpisodes", True):
            return None

        parent_url, qs = self.parentItem.url.split("?", 1)
        url = "{}/seasons/{}/episodes?apiKey={}".format(parent_url, season_id, self.__api_key)
        item = mediaitem.MediaItem(title, url)
        item.type = 'folder'
        item.thumb = self.parentItem.thumb
        item.fanart = self.parentItem.fanart
        return item

    def CreateSeriesVideoItem(self, result_set):
        title = result_set["title"]
        sub_title = result_set.get("episodeTitle", None)
        if sub_title:
            title = "{} - {}".format(title, sub_title)

        if not result_set["usageRights"].get("hasRightsNow", True):
            Logger.Debug("Found '%s' without 'usageRights'", title)
            return None

        url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(result_set["id"], self.__api_key)
        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.thumb = self.__get_image(result_set["image"]["webImages"], "pixelWidth", "imageUrl")
        item.description = result_set.get("longDescription", "")
        if not item.description:
            item.description = result_set.get("shortDescription", "")

        item.isGeoLocked = result_set.get("usageRights", {}).get("isGeoBlocked", False)
        self.__set_date(result_set, item)
        return item

    def CreateInstalmentSeasonItem(self, result_set):
        title = result_set["title"]
        season_id = result_set["name"]
        if title != season_id:
            title = "{} - {}".format(season_id, title)

        # if not result_set.get("hasOnDemandRightsEpisodes", True):
        #     return None

        url = "{}{}?apiKey={}".format(self.baseUrl, result_set["href"], self.__api_key)

        # parent_url, qs = self.parentItem.url.split("?", 1)
        # url = "{}/seasons/{}/Episodes?apiKey={}".format(parent_url, season_id, self.__api_key)
        item = mediaitem.MediaItem(title, url)
        item.type = 'folder'
        item.thumb = self.parentItem.thumb
        item.fanart = self.parentItem.fanart
        return item

    def CreateInstalmentVideoItem(self, result_set):
        title = result_set["titles"]["title"]
        sub_title = result_set["titles"]["subtitle"]
        # if sub_title and sub_title.strip():
        #     title = "{} - {}".format(title, sub_title)

        if result_set.get("availability", {}).get("status", "available") != "available":
            Logger.Debug("Found '%s' with a non-available status", title)
            return None

        url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(result_set["prfId"], self.__api_key)
        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.thumb = self.__get_image(result_set["image"], "width", "url")
        item.fanart = self.parentItem.fanart
        item.isGeoLocked = result_set.get("usageRights", {}).get("geoBlock", {}).get("isGeoBlocked", False)
        if sub_title and sub_title.strip():
            item.description = sub_title

        if "firstTransmissionDateDisplayValue" in result_set:
            Logger.Trace("Using 'firstTransmissionDateDisplayValue' for date")
            day, month, year = result_set["firstTransmissionDateDisplayValue"].split(".")
            item.SetDate(year, month, day)
        elif "usageRights" in result_set and "from" in result_set["usageRights"] and result_set["usageRights"]["from"] is not None:
            Logger.Trace("Using 'usageRights.from.date' for date")
            date_value = result_set["usageRights"]["from"]["date"].split("+")[0]
            time_stamp = DateHelper.get_date_from_string(date_value, date_format="%Y-%m-%dT%H:%M:%S")
            item.SetDate(*time_stamp[0:6])

        return item

    def CreateLiveChannelItem(self, result_set):
        url = "{}{}?apiKey={}".format(self.baseUrl, result_set["_links"]["manifest"]["href"], self.__api_key)

        live_data = result_set["_embedded"]["playback"]
        item = mediaitem.MediaItem(live_data["title"], url)
        item.type = "video"
        item.isLive = True
        item.isGeoLocked = live_data.get("isGeoBlocked")
        self.__get_image(live_data["posters"][0]["image"]["items"], "pixelWidth", "url")
        return item

    def UpdateLiveChannel(self, item):
        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.Open(item.url, proxy=self.proxy, noCache=True, additionalHeaders=headers)
        manifest = JsonHelper(data)
        if "nonPlayable" in manifest.json and manifest.json["nonPlayable"]:
            Logger.Error("Cannot update Live: %s", item)
            return item

        source = manifest.GetValue("sourceMedium")
        if source == "audio":
            return self.__update_live_audio(item, manifest, headers)
        else:
            return self.__update_live_video(item, manifest, headers)

    def UpdateJsonVideoItem(self, item):
        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=headers)
        video_data = JsonHelper(data)
        stream_data = video_data.GetValue("mediaAssetsOnDemand")
        if not stream_data:
            return item

        use_adaptive = AddonSettings.UseAdaptiveStreamAddOn()
        stream_data = stream_data[0]
        part = item.CreateNewEmptyMediaPart()
        if "hlsUrl" in stream_data:
            hls_url = stream_data["hlsUrl"]
            if use_adaptive:
                stream = part.AppendMediaStream(hls_url, 0)
                M3u8.SetInputStreamAddonInput(stream, self.proxy, headers=headers)
                item.complete = True
            else:
                for s, b in M3u8.GetStreamsFromM3u8(hls_url, self.proxy, headers=headers):
                    item.complete = True
                    # s = self.GetVerifiableVideoUrl(s)
                    part.AppendMediaStream(s, b)

        if "timedTextSubtitlesUrl" in stream_data and stream_data["timedTextSubtitlesUrl"]:
            sub_url = stream_data["timedTextSubtitlesUrl"].replace(".ttml", ".vtt")
            sub_url = HtmlEntityHelper.url_decode(sub_url)
            part.Subtitle = SubtitleHelper.DownloadSubtitle(sub_url, format="webvtt")
        return item

    def __update_live_audio(self, item, manifest, headers):
        video_info = manifest.GetValue("playable", "assets", 0)
        url = video_info["url"]
        # encrypted = video_info["encrypted"]
        part = item.CreateNewEmptyMediaPart()

        # Adaptive add-on does not work with audio only
        for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy, headers=headers):
            item.complete = True
            part.AppendMediaStream(s, b)

        return item

    def __update_live_video(self, item, manifest, headers):
        video_info = manifest.GetValue("playable", "assets", 0)
        url = video_info["url"]
        encrypted = video_info["encrypted"]
        part = item.CreateNewEmptyMediaPart()

        if encrypted:
            use_adaptive = AddonSettings.UseAdaptiveStreamAddOn(withEncryption=True)
            if not use_adaptive:
                Logger.Error("Cannot playback encrypted item without inputstream.adaptive with encryption support")
                return item
            stream = part.AppendMediaStream(url, 0)
            key = M3u8.GetLicenseKey("", keyHeaders=headers, keyType="R")
            M3u8.SetInputStreamAddonInput(stream, proxy=self.proxy, headers=headers, licenseKey=key)
            item.complete = True
        else:
            use_adaptive = AddonSettings.UseAdaptiveStreamAddOn(withEncryption=False)
            if use_adaptive:
                stream = part.AppendMediaStream(url, 0)
                M3u8.SetInputStreamAddonInput(stream, self.proxy, headers=headers)
                item.complete = True
            else:
                for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy, headers=headers):
                    item.complete = True
                    part.AppendMediaStream(s, b)

        return item

    def __set_date(self, result_set, item):
        if "usageRights" in result_set and "availableFrom" in result_set["usageRights"] \
                and result_set["usageRights"]["availableFrom"] is not None:
            Logger.Trace("Using 'usageRights.availableFrom' for date")
            # availableFrom=/Date(1540612800000+0200)/
            epoch_stamp = result_set["usageRights"]["availableFrom"][6:16]
            available_from = DateHelper.get_date_from_posix(int(epoch_stamp))
            item.SetDate(available_from.year, available_from.month, available_from.day)

        elif "episodeNumberOrDate" in result_set and result_set["episodeNumberOrDate"] is not None:
            Logger.Trace("Using 'episodeNumberOrDate' for date")
            date_parts = result_set["episodeNumberOrDate"].split(".")
            if len(date_parts) == 3:
                item.SetDate(date_parts[2], date_parts[1], date_parts[0])

        elif "programUrlMetadata" in result_set and result_set["programUrlMetadata"] is not None:
            Logger.Trace("Using 'programUrlMetadata' for date")
            date_parts = result_set["programUrlMetadata"].split("-")
            if len(date_parts) == 3:
                item.SetDate(date_parts[2], date_parts[1], date_parts[0])
        return

    def __get_image(self, images, width_attribute, url_attribute):
        max_width = 0
        thumb = None
        for image_data in images:
            src = image_data[url_attribute]
            width = image_data[width_attribute]
            # if  width > max_width:
            #     item.fanart = src
            if max_width < width < 521:
                thumb = src

        return thumb
