# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
from typing import Union, List

import pytz

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.addonsettings import AddonSettings
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.authentication.gigyahandler import GigyaHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "videolandimage.png"
        self.poster = "videolandposter.png"

        # setup the urls
        self.mainListUri = "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/alias/home/layout?nbPages=1"

        self._add_data_parser(self.mainListUri, requires_logon=True, json=True,
                              name="Mainlist for Videoland",
                              parser=["blocks"], creator=self.create_main_list_item)

        self._add_data_parser("https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/",
                              name="Main folder processor", json=True, requires_logon=True,
                              parser=["content", "items"], creator=self.create_episode_item)

        # Authentication
        handler = GigyaHandler(
            "videoland.com", "3_t2Z1dFrbWR-IjcC-Bod1kei6W91UKmeiu3dETVG5iKaY4ILBRzVsmgRHWWo0fqqd",
            "4_hRanGnYDFjdiZQfh-ghhhg", AddonSettings.get_client_id())
        self.__authenticator = Authenticator(handler)
        self.__jwt = None

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
        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        return item

    def create_episode_item(self, result_set: Union[str, dict]) -> Union[MediaItem, List[MediaItem], None]:
        result_set: dict = result_set["itemContent"]

        title = result_set["title"]
        extra_title = result_set.get("extraTitle")
        if extra_title:
            title = f"{title} - {extra_title}"
        show_id = result_set["id"]
        item = MediaItem(title, show_id, media_type=mediatype.EPISODE)

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

        date_value = result_set["details"].lower()
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

        action = result_set.get("action", {}).get("label", "").lower()
        item.isPaid = action == "abonneren"
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
        username = self._get_setting("videolandnl_username", value_for_none=None)
        result = self.__authenticator.log_on(username=username, channel_guid=self.guid, setting_id="videolandnl_password")

        if not username:
            Logger.info("No username for Videoland specified. Not logging in.")
            # Return True to prevent unwanted messages
            return False

        self.__jwt = self.__authenticator.get_authentication_token()
        self.httpHeaders["Authorization"] = f"Bearer {self.__jwt}"
        return result.logged_on
