#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import sys
import xbmc
import xbmcgui

from config import Config
from logger import Logger
from helpers.sessionhelper import SessionHelper
from helpers.channelimporter import ChannelIndex
from addonsettings import AddonSettings

# only append if there are no active sessions
if not SessionHelper.IsSessionActive():
    # first call in the session, so do not append the log
    appendLogFile = False
else:
    appendLogFile = True

Logger.CreateLogger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                    Config.appName,
                    append=appendLogFile,
                    dualLogger=lambda x, y=4: xbmc.log(x, y))


class Menu(object):
    @staticmethod
    def SelectChannels():
        multiSelectValues = ChannelIndex.GetRegister().GetChannels(includeDisabled=True)
        enabledChannels = filter(lambda c: c.enabled, multiSelectValues)

        enabledListItems = map(lambda c: c.safeName, enabledChannels)
        selectedIndices = map(lambda c: multiSelectValues.index(c), enabledChannels)

        dialog = xbmcgui.Dialog()
        selectedChannels = dialog.multiselect("Select Enabled Channels", enabledListItems,
                                              preselect=selectedIndices)

    @staticmethod
    def ShowSettings():
        AddonSettings.ShowSettings()

    @staticmethod
    def ChannelSettings():
        item = sys.listitem
        guid = item.getProperty("Retrospect")
        Logger.Debug("Fetching channel %s", guid)
        channel = ChannelIndex.GetRegister().GetChannel()

        from addonsettings import AddonSettings
        AddonSettings.ShowChannelSettings(channel)
        pass

