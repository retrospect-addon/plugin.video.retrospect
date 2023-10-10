# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from typing import Dict, Union, Any, Optional, List

import pytz

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.authentication.rtlxlhandler import RtlXlHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import FolderItem
from resources.lib.mediaitem import MediaItem
from resources.lib.parserdata import ParserData
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
        self.noImage = "videolandimage.png"
        self.poster = "videolandposter.png"

        # setup the urls
        self.mainListUri = "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/alias/home/layout?nbPages=2"

        #===============================================================================================================
        # non standard items
        self.__ignore_cookie_law()
        self.__timezone = pytz.timezone("Europe/Amsterdam")

    def __ignore_cookie_law(self):
        """ Accepts the cookies from RTL channel in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.set_cookie(name='rtlcookieconsent', value='yes', domain='.www.rtl.nl')
        return
