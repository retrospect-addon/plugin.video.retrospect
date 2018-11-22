# coding:UTF-8
import datetime

import mediaitem
import chn_class

from helpers.datehelper import DateHelper
from logger import Logger
from parserdata import ParserData
from urihandler import UriHandler
from regexer import Regexer
from helpers.jsonhelper import JsonHelper


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

        if self.channelCode == "pathejson":
            # we need to add headers and stuff for the API
            # self.UriHandlerOpen = UriHandler.open
            # UriHandler.open = self.__JsonHandlerOpen

            self.baseUrl = "https://connect.pathe.nl/v1"
            # set the default headers
            self.httpHeaders = {"X-Client-Token": "2d1411a8ec9842988e2700a1e3180dd3",
                                "Accept": "application/json"}
            self.mainListUri = "https://connect.pathe.nl/v1/cinemas"

            self._add_data_parser("https://connect.pathe.nl/v1/cinemas", json=True, match_type=ParserData.MatchExact,
                                  parser=[], creator=self.CreateCinema)
            self._add_data_parser("/movies/nowplaying", json=True, match_type=ParserData.MatchEnd,
                                  parser=[], creator=self.CreateMovie)
            self._add_data_parser("https://connect.pathe.nl/v1/movies/", json=True,
                                  parser=['trailers'], creator=self.CreateTrailer)
            self._add_data_parser("/schedules?date=", json=True, match_type=ParserData.MatchContains,
                                  preprocessor=self.GetScheduleData, parser=['movies'], creator=self.CreateMovie)

        elif self.channelCode == "pathe":
            self.mainListUri = "https://www.pathe.nl"
            self.baseUrl = "https://www.pathe.nl"
            # setup the main parsing data
            self.episodeItemRegex = '<li><a[^>]+href="(https://www.pathe.nl/bioscoop/[^"]+)"[^>]+>([^<]+)</a></li>'
            self.folderItemRegex = '<li class="tab-item[^>]+>\W+<a[^>]+title="\w+ (\d+) (\w+) (\d+)"[^<]+' \
                                   'href="([^#]+)#schedule[^>]*>(\w+)'
            self.videoItemRegex = '<div class="schedule-movie">\W+<a[^>]+href="([^#]+)\#[^>]+"[^>]+' \
                                  'title="([^"]+)"[^>]+>\W+<div[^>]+>\W+<img[^>]+src="([^"]+)"[^>]+>\W+</div>' \
                                  '[\w\W]{0,1500}?<table class="table-schedule">([\w\W]{0,5000}?)</table>'
            self.mediaUrlRegex = 'file: "(http[^"]+)'

        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "patheimage.png"
        self.scheduleData = None

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateCinema(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """
        Logger.trace(resultSet)
        cinema = mediaitem.MediaItem(resultSet["name"], "")
        cinema.icon = self.icon
        cinema.thumb = resultSet["image"].replace("nocropthumb/[format]/", "")
        cinema.complete = True

        nowPlayingUrl = "%s/cinemas/%s/movies/nowplaying" % (self.baseUrl, resultSet["id"])
        nowPlaying = mediaitem.MediaItem("Trailers", nowPlayingUrl)
        nowPlaying.icon = self.icon
        # https://www.pathe.nl/nocropthumb/[format]/gfx_content/bioscoop/foto/pathe.nl_380x218px_amersfoort.jpg
        nowPlaying.complete = True
        nowPlaying.HttpHeaders = self.httpHeaders
        cinema.items.append(nowPlaying)

        now = datetime.datetime.now()
        for i in range(0, 10):
            date = now + datetime.timedelta(days=i)
            title = "%s-%02d-%02d" % (date.year, date.month, date.day)
            scheduleUrl = "%s/cinemas/%s/schedules?date=%s" % (self.baseUrl, resultSet["id"], title)
            schedule = mediaitem.MediaItem("Agenda: %s" % (title,), scheduleUrl)
            schedule.icon = self.icon
            schedule.complete = True
            schedule.thumb = cinema.thumb
            schedule.HttpHeaders = self.httpHeaders
            cinema.items.append(schedule)
        return cinema

    def CreateMovie(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)
        movieId = resultSet['id']
        url = "%s/movies/%s" % (self.baseUrl, movieId)
        item = mediaitem.MediaItem(resultSet["name"], url)
        item.icon = self.icon
        item.thumb = resultSet["thumb"].replace("nocropthumb/[format]/", "")
        item.complete = True
        item.HttpHeaders = self.httpHeaders

        if self.scheduleData:
            Logger.debug("Adding schedule data")
            # scheduleData = filter(lambda s: s['movieId'] == movieId, self.scheduleData)
            scheduleData = [s for s in self.scheduleData if s['movieId'] == movieId]
            schedule = ""
            day = ""
            for s in scheduleData:
                start = s['start']
                day, start = start.split("T")
                hour, minute, ignore = start.split(":", 2)
                start = "%s:%s" % (hour, minute)

                end = s['end']
                ignore, end = end.split("T")
                hour, minute, ignore = end.split(":", 2)
                end = "%s:%s" % (hour, minute)

                schedule = "%s%s-%s, " % (schedule, start, end)
            item.description = "%s\n\n%s: %s" % (item.description, day, schedule.strip(', '))

        item.description = "%s\n\n%s" % (item.description, resultSet.get('teaser', ""))
        if not item.description.endswith('.'):
            item.description = "%s." % (item.description, )

        if "releaseDate" in resultSet:
            item.description = "%s\n\nRelease datum: %s" % (item.description, resultSet["releaseDate"])

        # date = resultSet.get('releaseDate', None)
        # if date is not None:
        #     year, month, day = date.split("-")
        #     item.set_date(year, month, day)

        item.description = item.description.strip()
        return item

    def CreateTrailer(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)
        url = self.parentItem.url
        item = mediaitem.MediaItem(resultSet["caption"], url, "video")
        item.icon = self.icon
        item.thumb = resultSet["still"].replace("nocropthumb/[format]/", "")
        item.fanart = item.thumb
        item.append_single_stream(resultSet['filename'])
        item.complete = True
        item.HttpHeaders = self.httpHeaders
        return item

    def GetScheduleData(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.info("Performing Pre-Processing")
        items = []
        json = JsonHelper(data)
        self.scheduleData = json.get_value("schedules")
        Logger.debug("Pre-Processing finished")
        return data, items

    def create_episode_item(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """

        item = mediaitem.MediaItem(resultSet[1], resultSet[0])
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def create_folder_item(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.
        
        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex
        
        Returns:
        A new MediaItem of type 'folder'
        
        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes 
        and are specific to the channel.
         
        """

        Logger.trace(resultSet)

        if self.parentItem.url.endswith(str(DateHelper.this_year())):
            return None

        url = "%s%s" % (self.baseUrl, resultSet[3])
        name = resultSet[4]

        item = mediaitem.MediaItem(name.title(), url)
        item.thumb = self.noImage
        item.icon = self.icon

        day = resultSet[0]
        month = resultSet[1]
        month = DateHelper.get_month_from_name(month, "nl", short=False)
        year = resultSet[2]

        item.set_date(year, month, day)
        item.complete = True
        return item
    
    def create_video_item(self, resultSet):
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.
         
        """

        Logger.trace(resultSet)

        if not self.parentItem.url[-1].isdigit():
            # only video on folders for day
            return None

        name = resultSet[1]
        url = "%s%s" % (self.baseUrl, resultSet[0])

        thumbUrl = resultSet[2]
        if not thumbUrl.startswith("http"):
            thumbUrl = "%s%s" % (self.baseUrl, thumbUrl)
        # https://www.pathe.nl/gfx_content/posters/clubvansinterklaas3p1.jpg
        # https://www.pathe.nl/nocropthumb/180x254/gfx_content/posters/clubvansinterklaas3p1.jpg
        thumbUrl = thumbUrl.replace("nocropthumb/180x254/", "")

        item = mediaitem.MediaItem(name, url)
        item.thumb = thumbUrl
        item.icon = self.icon
        item.type = 'video'

        # more description stuff
        # description = "%s\n\n" % (resultSet[4],)
        description = ""
        
        timeTable = resultSet[3]
        timeTableRegex = '<ul>\W+<li><b>([^<]+)</b></li>\W+<li>\w+ (\d+:\d+)</li>\W+<li>\w+ (\d+:\d+)</li>'
        biosSet = False
        for timeTableEntry in Regexer.do_regex(timeTableRegex, timeTable):
            Logger.trace(timeTableEntry)

            bios = timeTableEntry[0]
            if not biosSet:
                description = "%s%s: " % (description, bios)
                biosSet = True

            startTime = timeTableEntry[1]
            endTime = timeTableEntry[2]
            description = "%s%s-%s, " % (description, startTime, endTime)

        description = description.strip(', ')
        item.description = description.strip()
        
        item.complete = False        
        return item
    
    def update_video_item(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)
        
        data = UriHandler.open(item.url, proxy=self.proxy)
        videos = Regexer.do_regex(self.mediaUrlRegex, data)

        fanart = Regexer.do_regex('<div class="visual-image">\W+<img src="([^"]+)"', data)
        if fanart:
            item.fanart = fanart[0]

        for video in videos:
            Logger.trace(video)
            item.append_single_stream(video)
        
        item.complete = True
        return item

    # def __JsonHandlerOpen(self, uri, proxy=None, maxBytes=0, params="", referer=None, additionalHeaders=None, noCache=False, progressCallback=None):
    #     """ Used to append headers for the JSON api calls
    #
    #     @param uri:
    #     @param proxy:
    #     @param maxBytes:
    #     @param params:
    #     @param referer:
    #     @param additionalHeaders:
    #     @param noCache:
    #     @param progressCallback:
    #     @return:
    #     """
    #     Logger.Debug("Using Custom UriHandler with extra headers")
    #     if additionalHeaders is None:
    #         additionalHeaders = dict()
    #
    #     additionalHeaders["X-Client-Token"] = "2d1411a8ec9842988e2700a1e3180dd3"
    #     additionalHeaders["Accept"] = "application/json"
    #     return self.UriHandlerOpen(uri, proxy, maxBytes, params, referer, additionalHeaders, noCache, progressCallback)


# https://connect.pathe.nl/v1/cinemas/8/schedules?date=2014-11-26

#     httpclient = getHttpClient();
# ((HttpUriRequest) (obj)).setHeader("User-Agent", PatheApplication.USER_AGENT);
# ((HttpUriRequest) (obj)).setHeader("Accept", "application/json");
# ((HttpUriRequest) (obj)).setHeader("Accept-Language", "nl-NL");
# ((HttpUriRequest) (obj)).setHeader("X-Client-Token", "2d1411a8ec9842988e2700a1e3180dd3");
# ((HttpUriRequest) (obj)).setHeader("X-Device-Token", PatheApplication.DEVICE_TOKEN);
# ((HttpUriRequest) (obj)).setHeader("X-Device-Type", "Android");
# ((HttpUriRequest) (obj)).setHeader("X-Site-Id", "2");
# ((HttpUriRequest) (obj)).setHeader("X-Operating-System", "Android");
# ((HttpUriRequest) (obj)).setHeader("X-System-Version", android.os.Build.VERSION.RELEASE);
# ((HttpUriRequest) (obj)).setHeader("X-Software-Version", PatheApplication.APP_VERSION);
# if (list1 != null)

# // Decompiled by Jad v1.5.8e. Copyright 2001 Pavel Kouznetsov.
# // Jad home page: http://www.geocities.com/kpdus/jad.html
# // Decompiler options: braces fieldsfirst space lnc
#
# package net.sharewire.pathe2013.utils;
#
# import java.util.Arrays;
# import java.util.List;
#
# public interface Constants
# {
#
#     public static final String ANALYTICS_CONTAINER_ID_PHONE = "GTM-KRHKHG";
#     public static final String ANALYTICS_CONTAINER_ID_TABLET = "GTM-WXKNSS";
#     public static final String API_DEBUG_URL = "http://pathe-api.accept.poort80.net/";
#     public static final String API_HEADER_ACCEPT_LANGUAGE = "nl-NL";
#     public static final String API_HEADER_CLIENT_TOKEN = "2d1411a8ec9842988e2700a1e3180dd3";
#     public static final String API_HEADER_SITE_ID = "2";
#     public static final String API_HEADER_X_OPERATING_SYSTEM_VALUE = "Android";
#     public static final String API_HEADER_X_SYSTEM_VERSION_VALUE = (new StringBuilder()).append(android.os.Build.VERSION.RELEASE).toString();
#     public static final String API_IMAGE_FORMAT_TAG = "[format]";
#     public static final String API_PRODUCTION_URL = "https://connect.pathe.nl/v1/";
#     public static final String API_URL_ARTICLE_BY_CODE = "articles/code/%s";
#     public static final String API_URL_CINEMA = "cinemas/%d";
#     public static final String API_URL_CINEMAS = "cinemas";
#     public static final String API_URL_CINEMA_EVENTS = "cinemas/%d/events";
#     public static final String API_URL_CINEMA_MOVIES_NOWPLAYING = "cinemas/%d/movies/nowplaying";
#     public static final String API_URL_CINEMA_SCHEDULES = "cinemas/%d/schedules";
#     public static final String API_URL_CINEMA_SPECIALS = "cinemas/%d/specials";
#     public static final String API_URL_CINEMA_TRAILERS = "cinemas/%d/trailers";
#     public static final String API_URL_DEVICE = "devices/%s";
#     public static final String API_URL_DEVICE_NOTIFICATIONS = "devices/%s/notifications";
#     public static final String API_URL_DEVICE_NOTIFICATIONS_SINGLE = "devices/%s/notifications/%d";
#     public static final String API_URL_FAQ = "faq";
#     public static final String API_URL_GENRES = "genres";
#     public static final String API_URL_GET_SEAT_SELECTION = "transactions/%d/seats";
#     public static final String API_URL_MOVIES = "movies/%d";
#     public static final String API_URL_MOVIES_LIST_BY_TYPE = "movies/%s";
#     public static final String API_URL_MOVIES_OVERVIEW = "movies/overview";
#     public static final String API_URL_MOVIES_RATINGS = "movies/%d/ratings";
#     public static final String API_URL_MOVIES_SEARCH = "movies/nowplaying/search/";
#     public static final String API_URL_MOVIE_PER_CINEMA_SCHEDULES = "movies/%d/schedules";
#     public static final String API_URL_NOTIFICATIONS = "notifications";
#     public static final String API_URL_PERSON = "people/%d";
#     public static final String API_URL_PUT_SEAT_SELECTION = "transactions/%d/seats/%s";
#     public static final String API_URL_QUICKSEARCH = "quicksearch";
#     public static final String API_URL_QUICKSEARCH_NOW_PLAYING = "quicksearch/movies/nowplaying";
#     public static final String API_URL_SCHEDULE_TICKETS = "schedules/%d/tickets";
#     public static final String API_URL_SESSIONS = "sessions";
#     public static final String API_URL_SESSIONS_BY_ID = "sessions/%d";
#     public static final String API_URL_SESSIONS_FACEBOOK = "sessions/facebook";
#     public static final String API_URL_SPECIAL = "specials/%d";
#     public static final String API_URL_SPECIALS = "specials";
#     public static final String API_URL_SPLASH = "splash/current";
#     public static final String API_URL_TILES_MOBILE = "tiles/mobile";
#     public static final String API_URL_TILES_TABLET = "tiles/tablet";
#     public static final String API_URL_TRAILERS = "trailers/new";
#     public static final String API_URL_USER = "users/%d";
#     public static final String API_URL_USERS_FACEBOOK = "users/facebook";
#     public static final String API_URL_USER_CINEMAS = "users/%d/cinemas";
#     public static final String API_URL_USER_FAVORITES = "users/%d/movies/favorites";
#     public static final String API_URL_USER_FAVORITES_BY_ID = "users/%d/movies/favorites/%d";
#     public static final String API_URL_USER_USERDATA = "users/%d/favorites";
#     public static final long CACHE_DEFAULT_EXPIRETIME = 0x36ee80L;
#     public static final long CACHE_DONT_SAVE = -1L;
#     public static final long CACHE_SAVE_FOREVER = -2L;
#     public static final boolean DEBUG_MODE = false;
#     public static final List FACEBOOK_PERMISSIONS_PUBLISH = Arrays.asList(new String[] {
#         "publish_stream"
#     });
#     public static final List FACEBOOK_PERMISSIONS_READ = Arrays.asList(new String[] {
#         "basic_info", "email", "user_about_me", "user_birthday", "user_hometown", "user_location"
#     });
#     public static final String FILE_IMG_DIR = "pathe_images/";
#     public static final int FILL_SCREEN = -1;
#     public static final String GCM_SENDER_ID = "514389178028";
#     public static final String HOME_TIMEZONE = "Europe/Amsterdam";
#     public static final String INTENT_KEY_IMG_URL = "INTENT_KEY_IMG_URL";
#     public static final String INTENT_KEY_OBJ_CINEMA = "INTENT_KEY_OBJ_CINEMA";
#     public static final String INTENT_KEY_OBJ_CINEMA_LIST = "INTENT_KEY_OBJ_CINEMA_LIST";
#     public static final String INTENT_KEY_OBJ_CINEMA_SCHEDULE = "INTENT_KEY_OBJ_CINEMA_SCHEDULE";
#     public static final String INTENT_KEY_OBJ_MOVIE = "INTENT_KEY_OBJ_MOVIE";
#     public static final String INTENT_KEY_OBJ_PATHE_PERSON = "INTENT_KEY_OBJ_PATHE_PERSON";
#     public static final String INTENT_KEY_OBJ_SCHEDULE = "INTENT_KEY_OBJ_SCHEDULE";
#     public static final String INTENT_KEY_OBJ_SEATS = "INTENT_KEY_OBJ_SEATS";
#     public static final String INTENT_KEY_OBJ_SPECIAL = "INTENT_KEY_OBJ_SPECIAL";
#     public static final String INTENT_KEY_OBJ_TICKETS_FOR_SCHEDULE = "INTENT_KEY_OBJ_TICKETS_FOR_SCHEDULE";
#     public static final String INTENT_KEY_OBJ_TRANSACTION = "INTENT_KEY_OBJ_TRANSACTION";
#     public static final String INTENT_KEY_OPEN_MY_CINEMAS = "INTENT_KEY_OPEN_MY_CINEMAS";
#     public static final String INTENT_KEY_OPEN_MY_FAVORITES = "INTENT_KEY_OPEN_MY_FAVORITES";
#     public static final String INTENT_KEY_TIMELINE_CURRENT_CINEMA = "INTENT_KEY_TIMELINE_CURRENT_CINEMA";
#     public static final String INTENT_KEY_TIMELINE_CURRENT_DAY = "INTENT_KEY_TIMELINE_CURRENT_DAY";
#     public static final String INTENT_KEY_TIMELINE_FILTER = "INTENT_KEY_TIMELINE_FILTER";
#     public static final String INTENT_KEY_VALUE_ANALYTICS_SCREEN_NAME = "INTENT_KEY_VALUE_ANALYTICS_SCREEN_NAME";
#     public static final String INTENT_KEY_VALUE_CINEMA_ID = "INTENT_KEY_VALUE_CINEMA_ID";
#     public static final String INTENT_KEY_VALUE_DAY_OFFSET = "INTENT_KEY_VALUE_DAY_OFFSET";
#     public static final String INTENT_KEY_VALUE_FILTER_CINEMAS = "INTENT_KEY_VALUE_FILTER_CINEMEAS";
#     public static final String INTENT_KEY_VALUE_FILTER_ORDER = "INTENT_KEY_VALUE_FILTER_ORDER";
#     public static final String INTENT_KEY_VALUE_FRAGMENT_TAG = "INTENT_KEY_FRAGMENT_TAG";
#     public static final String INTENT_KEY_VALUE_MOVIES_LIST_TYPE = "INTENT_KEY_VALUE_MOVIES_LIST_TYPE";
#     public static final String INTENT_KEY_VALUE_MOVIE_ID = "INTENT_KEY_VALUE_MOVIE_ID";
#     public static final String INTENT_KEY_VALUE_NUM_SEATS = "INTENT_VALUE_NUM_SEATS";
#     public static final String INTENT_KEY_VALUE_PATHE_PERSON_ID = "INTENT_KEY_VALUE_PATHE_PERSON_ID";
#     public static final String INTENT_KEY_VALUE_PATHE_PERSON_POSITION = "INTENT_KEY_VALUE_PATHE_PERSON_POSITION";
#     public static final String INTENT_KEY_VALUE_PAYMENT_URL = "PREF_KEY_VALUE_PAYMENT_URL";
#     public static final String INTENT_KEY_VALUE_PERSON_TYPE = "INTENT_KEY_VALUE_PERSON_TYPE";
#     public static final String INTENT_KEY_VALUE_SCHEDULE_ID = "INTENT_KEY_VALUE_SCHEDULE_ID";
#     public static final String INTENT_KEY_VALUE_SHOW_GPS_DIALOG = "INTENT_KEY_VALUE_SHOW_GPS_DIALOG";
#     public static final String INTENT_KEY_VALUE_SPECIAL_ID = "INTENT_VALUE_SPECIAL_ID";
#     public static final String INTENT_KEY_VALUE_TITLE = "PREF_KEY_VALUE_TITLE";
#     public static final String INTENT_KEY_VALUE_VIDEO_NAME = "INTENT_KEY_VALUE_VIDEO_NAME";
#     public static final String INTENT_KEY_VALUE_VIDEO_PROGRESS = "INTENT_KEY_TRAILER_PROGRESS";
#     public static final String INTENT_KEY_VALUE_VIDEO_URL = "INTENT_KEY_VALUE_VIDEO_URL";
#     public static final long LOCATION_TIMEOUT = 60000L;
#     public static final String LOGTAG = "Pathe2013";
#     public static final int MOVIE_INFO_BANNER_IMAGE_DELAY = 6000;
#     public static final String MOVIE_LIST_TYPE_COMINGSOON = "comingsoon";
#     public static final String MOVIE_LIST_TYPE_NOWPLAYING = "nowplaying";
#     public static final String MOVIE_LIST_TYPE_OVERVIEW = "overview";
#     public static final String MOVIE_LIST_TYPE_TOP10 = "top10";
#     public static final String MOVIE_LIST_TYPE_VOD = "vod";
#     public static final String NFC_MIME_TYPE = "application/json+pathe-ticket";
#     public static final int NOTIFICATION_DEFAULT_MINUTES_BEFORE = 10;
#     public static final long NOTIFICATION_ID_NEW_MOVIE_PREMIERE = 1L;
#     public static final long NOTIFICATION_ID_RATE_MOVIE = 3L;
#     public static final long NOTIFICATION_ID_START_MOVIE = 4L;
#     public static final int NOTIFICATION_MINUTES_OPTIONS[] = {
#         10, 60, 120, 1440
#     };
#     public static final String NOTIFICATION_START_MOVIE = "start_movie";
#     public static final double PATHE_ASPECT_RATIO_MOVIE_POSTER_WIDTH_TO_HEIGHT = 1.4099999999999999D;
#     public static final double PATHE_ASPECT_RATIO_MOVIE_TRAILER_WIDTH_TO_HEIGHT = 0.5625D;
#     public static final String PATHE_NL_PREFIX = "http://www.pathe.nl/";
#     public static final String PREF_FLAG_HAS_MIGRATED = "PREF_FLAG_HAS_MIGRATED";
#     public static final String PREF_KEY_DIALOG_GPS_SKIP = "PREF_KEY_DIALOG_GPS_SKIP";
#     public static final String PREF_KEY_GCM_APP_VERSION = "PREF_KEY_GCM_APP_VERSION";
#     public static final String PREF_KEY_GCM_REG_ID = "PREF_KEY_GCM_REG_ID";
#     public static final String PREF_KEY_OBJ_SESSION = "PREF_KEY_OBJ_SESSION";
#     public static final String PREF_KEY_USERDATA_VERSION = "PREF_KEY_USERDATA_VERSION";
#     public static final String PREF_KEY_VALUE_CINEMA_ID = "PREF_KEY_VALUE_CINEMA_ID";
#     public static final String PREF_KEY_VALUE_FORCE_PROD_API = "PREF_KEY_VALUE_FORCE_PROD_API";
#     public static final String PREF_KEY_VALUE_HOME_ANIMATION_DONE = "PREF_KEY_VALUE_HOME_ANIMATION_DONE";
#     public static final String PREF_KEY_VALUE_HOME_LAST_PAGE = "PREF_KEY_VALUE_HOME_LAST_PAGE";
#     public static final String PREF_KEY_VALUE_NO_ADS = "PREF_KEY_VALUE_NO_ADS";
#     public static final String PREF_KEY_VALUE_SPLASH_LAST_VERSION = "PREF_KEY_VALUE_SPLASH_LAST_VERSION";
#     public static final String PREF_KEY_VALUE_TICKETS_ANONYMOUS_ORDER_EMAIL = "PREF_KEY_VALUE_TICKETS_ANONYMOUS_ORDER_EMAIL";
#     public static final String PREF_KEY_VALUE_TICKETS_ANONYMOUS_ORDER_NAME = "PREF_KEY_VALUE_TICKETS_ANONYMOUS_ORDER_NAME";
#     public static final String PREF_KEY_VALUE_TICKETS_ANONYMOUS_SKIP = "PREF_KEY_VALUE_TICKETS_ANONYMOUS_SKIP";
#     public static final String PREF_SETTINGS = "PREF_SETTINGS";
#     public static final String PREF_SIDEBAR_WIDTH = "INTENT_KEY_VALUE_SIDEBAR_WIDTH";
#     public static final boolean RELEASE_MODE = true;
#     public static final int REQUEST_BARCODE = 1001;
#     public static final int REQUEST_EMAIL_TICKET = 1003;
#     public static final int REQUEST_FILTER_CINEMA = 1004;
#     public static final int REQUEST_FILTER_MOVIE = 1005;
#     public static final int REQUEST_LOGIN = 1002;
#     public static final int REQUEST_ORDER_MOVIE = 1006;
#     public static final int REQUEST_SEAT_SELECTION = 1000;
#     public static final long TIME_DAY = 0x5265c00L;
#     public static final long TIME_HOUR = 0x36ee80L;
#     public static final long TIME_MINUTE = 60000L;
#     public static final long TIME_MONTH = 0x90321000L;
#     public static final long TIME_SECOND = 1000L;
#     public static final long TIME_WEEK = 0x240c8400L;
#
# }
