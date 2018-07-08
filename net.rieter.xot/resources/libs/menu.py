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
Logger.Info("****** Starting menu for %s add-on version %s *******", Config.appName, Config.version)


class Menu(object):
    def __init__(self):
        # noinspection PyUnresolvedReferences
        self.item = sys.listitem

    def SelectChannels(self):
        multiSelectValues = ChannelIndex.GetRegister().GetChannels(includeDisabled=True)
        enabledChannels = filter(lambda c: c.enabled, multiSelectValues)

        enabledListItems = map(lambda c: c.safeName, enabledChannels)
        selectedIndices = map(lambda c: multiSelectValues.index(c), enabledChannels)

        dialog = xbmcgui.Dialog()
        selectedChannels = dialog.multiselect("Select Enabled Channels", enabledListItems,
                                              preselect=selectedIndices)

        # TODO: we actually need to do something with them
        return selectedChannels

    def ShowSettings(self):
        AddonSettings.ShowSettings()

    def ChannelSettings(self):
        channel = self.__GetChannel()
        AddonSettings.ShowChannelSettings(channel)
        pass

    def __GetChannel(self):
        # noinspection PyUnresolvedReferences
        chn, code = self.item.getProperty("Retrospect").split("|")
        # chn = "chn_nos2010"
        # code = "uzgjson"
        code = code or None
        Logger.Debug("Fetching channel %s - %s", chn, code)
        channel = ChannelIndex.GetRegister().GetChannel(chn, code, infoOnly=True)
        return channel
