# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
from typing import Union, List, Optional

import pytz

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.addonsettings import AddonSettings
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.authentication.gigyahandler import GigyaHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler
from resources.lib.xbmcwrapper import XbmcWrapper


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "videolandnl-thumb.jpg"

        # setup the urls
        self.mainListUri = "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/alias/home/layout?nbPages=1"
        # https://pc.middleware.videoland.bedrock.tech/6play/v2/platforms/m6group_web/services/videoland/programs?limit=999&offset=0&csa=tot_18_jaar&with=rights

        self._add_data_parser(self.mainListUri, requires_logon=True, json=True,
                              name="Mainlist for Videoland",
                              parser=["blocks"], creator=self.create_main_list_item)

        self._add_data_parser("https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/",
                              name="Main folder processor", json=True, requires_logon=True,
                              parser=["content", "items"], creator=self.create_episode_item)

        self._add_data_parser("https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/video/", requires_logon=True,
                              name="Video updater", json=True, updater=self.update_video_item)

        # Authentication
        handler = GigyaHandler(
            "videoland.com", "3_t2Z1dFrbWR-IjcC-Bod1kei6W91UKmeiu3dETVG5iKaY4ILBRzVsmgRHWWo0fqqd",
            "4_hRanGnYDFjdiZQfh-ghhhg", AddonSettings.get_client_id())
        self.__authenticator = Authenticator(handler)
        self.__jwt = None
        self.__uid = None

        #===============================================================================================================
        # non standard items
        self.__ignore_cookie_law()
        self.__pages = 10
        self.__timezone = pytz.timezone("Europe/Amsterdam")

    def create_main_list_item(self, result_set: Union[str, dict]) -> Union[MediaItem, List[MediaItem], None]:
        if not result_set["title"]:
            return None
        title = result_set["title"].get("long", result_set["title"].get("short"))
        page_id = result_set["id"]
        url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/{page_id}?nbPages={self.__pages}"

        feature_id = result_set["featureId"]
        item = FolderItem(title, url, content_type=contenttype.EPISODES if feature_id.startswith("videos") else contenttype.TVSHOWS)
        return item

    def create_episode_item(self, result_set: Union[str, dict]) -> Union[MediaItem, List[MediaItem], None]:
        result_set: dict = result_set["itemContent"]

        title = result_set["title"]
        extra_title = result_set.get("extraTitle")
        if extra_title:
            title = f"{title} - {extra_title}"
        item_id = result_set["id"]

        # What type is it
        action_info = result_set.get("action", {})
        action = action_info.get("label", "").lower()
        if "content" in action:
            url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/{item_id}/layout?nbPages=2"
            item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
        else:
            video_id = action_info["target"]["value_layout"]["id"]
            url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/video/{video_id}/layout?nbPages=2"
            item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.isPaid = action == "abonneren"

        if "image" in result_set:
            for ratio, image_id in result_set["image"]["idsByRatio"].items():
                image_url = f"https://images-fio.videoland.bedrock.tech/v2/images/{image_id}/raw"
                if ratio == "16:9":
                    item.thumb = image_url
                    item.fanart = image_url
                elif ratio == "2:3":
                    item.poster = image_url

        time_value = result_set["highlight"]
        if time_value and "min" in time_value:
            # 20min or 1uur20min
            hours = 0
            mins = 0
            if "uur" in time_value:
                hours, others = time_value.split("uur")
                mins, _ = others.split("min")
            elif "min" in time_value:
                mins, _ = time_value.split("min")
            item.set_info_label(MediaItem.LabelDuration, 60 * int(hours) + int(mins))

        date_value = (result_set["details"] or "").lower()
        if date_value:
            if date_value == "vandaag":
                # Vandaag
                time_stamp = datetime.datetime.now()
                item.set_date(time_stamp.year, time_stamp.month, time_stamp.day)
            elif date_value == "gisteren":
                # Gisteren
                time_stamp = datetime.datetime.now() - datetime.timedelta(days=1)
                item.set_date(time_stamp.year, time_stamp.month, time_stamp.day)
            elif date_value[-2].isnumeric():
                # 'Di 09 jan 24'
                weekday, day, month, year = date_value.split(" ")
                month = DateHelper.get_month_from_name(month, language="nl", short=True)
                year = 2000 + int(year)
                item.set_date(year, month, day)

        return item

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = JsonHelper(UriHandler.open(item.url, additional_headers=self.httpHeaders))
        video_info = data.get_value("blocks", 0, "content", "items", 0, "itemContent", "video")
        video_id = video_info["id"]

        # Construct license info
        license_token_url = f"https://drm.videoland.bedrock.tech/v1/customers/rtlnl/platforms/m6group_web/services/videoland_catchup/users/{self.__uid}/videos/{video_id}/upfront-token"
        license_token = JsonHelper(UriHandler.open(license_token_url, additional_headers=self.httpHeaders)).get_value("token")
        license_key = Mpd.get_license_key("https://lic.drmtoday.com/license-proxy-widevine/cenc/", key_headers={
            "x-dt-auth-token": license_token,
            "content-type": "application/octstream"
        }, json_filter="JBlicense")

        for asset in video_info["assets"]:
            quality = asset["video_quality"]
            url = asset["path"]
            video_type = asset["video_container"]

            if quality == "hd":
                continue

            if video_type == "mpd":
                stream = item.add_stream(url, 2000 if quality == "hd" else 1200)
                Mpd.set_input_stream_addon_input(stream, license_key=license_key)
                item.complete = True
            # elif video_type == "m3u8":
            #     # Not working in Kodi
            #     stream = item.add_stream(url, 2000 if quality == "hd" else 1200)
            #     item.complete = True
            #     M3u8.set_input_stream_addon_input(stream)
        return item

    def __ignore_cookie_law(self):
        """ Accepts the cookies from RTL channel in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.set_cookie(name='rtlcookieconsent', value='yes', domain='.www.rtl.nl')
        return

    def log_on(self):
        """ Logs on to a website, using an url.

        First checks if the channel requires log on. If so and it's not already
        logged on, it should handle the log on. That part should be implemented
        by the specific channel.

        More arguments can be passed on, but must be handled by custom code.

        After a successful log on the self.loggedOn property is set to True and
        True is returned.

        :return: indication if the login was successful.
        :rtype: bool

        """

        # Always try to log on. If the username was changed to empty, we should clear the current
        # log in.
        username: Optional[str] = self._get_setting("videolandnl_username", value_for_none=None)
        if not username:
            XbmcWrapper.show_dialog(None, LanguageHelper.MissingCredentials)

        result = self.__authenticator.log_on(username=username, channel_guid=self.guid, setting_id="videolandnl_password")

        # Set some defaults
        self.__jwt = self.__authenticator.get_authentication_token()
        self.__uid = result.uid
        self.httpHeaders["Authorization"] = f"Bearer {self.__jwt}"
        return result.logged_on
