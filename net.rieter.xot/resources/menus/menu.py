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

# we need to import the initializer
addOnPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(addOnPath)

# setup some initial stuff
from initializer import Initializer
Initializer.SetUnicode()
Initializer.SetupPythonPaths()
sys.path.remove(addOnPath)

from config import Config
from logger import Logger
Logger.CreateLogger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                    Config.appName,
                    append=True,
                    dualLogger=lambda x, y=4: xbmc.log(x, y))

from helpers.htmlentityhelper import HtmlEntityHelper
from addonsettings import AddonSettings, LOCAL
from favourites import Favourites
from paramparser import ParameterParser
from helpers.channelimporter import ChannelIndex
from helpers.languagehelper import LanguageHelper
from locker import LockWithDialog
from pickler import Pickler
from cloaker import Cloaker
from xbmcwrapper import XbmcWrapper
Logger.Instance().minLogLevel = AddonSettings.GetLogLevel()


class Menu(ParameterParser):

    def __init__(self, action):
        Logger.Info("**** Starting menu '%s' for %s add-on version %s ****",
                    action, Config.appName, Config.version)

        # noinspection PyUnresolvedReferences
        self.kodiItem = sys.listitem

        params = self.kodiItem.getPath()
        if not params:
            self.channelObject = None
            return

        name, params = params.split("?", 1)
        params = "?{0}".format(params)

        # Main constructor parses
        super(Menu, self).__init__(name, params)

        self.channelObject = self.__GetChannel()
        Logger.Debug("Plugin Params: %s (%s)\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params), self.pluginName, params)

        if self.keywordPickle in self.params:
            self.mediaItem = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        else:
            self.mediaItem = None

    def HideChannel(self):
        Logger.Info("Hiding channel: %s", self.channelObject)
        AddonSettings.SetChannelVisiblity(self.channelObject, False)
        self.Refresh()

    def SelectChannels(self):
        validChannels = ChannelIndex.GetRegister().GetChannels(includeDisabled=True)
        selectedChannels = filter(lambda c: c.enabled, validChannels)
        selectedIndices = map(lambda c: validChannels.index(c), selectedChannels)
        Logger.Debug("Currently selected channels: %s", selectedIndices)

        validChannelNames = map(lambda c: HtmlEntityHelper.ConvertHTMLEntities(c.channelName),
                                validChannels)

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelSelection)[:-1]
        selectedChannels = dialog.multiselect(heading, validChannelNames,
                                              preselect=selectedIndices)
        if selectedChannels is None:
            return

        selectedChannels = list(selectedChannels)
        Logger.Debug("New selected channels:       %s", selectedChannels)

        # TODO: we actually need to do something with them
        indicesToRemove = filter(lambda i: i not in selectedChannels, selectedIndices)
        indicesToAdd = filter(lambda i: i not in selectedIndices, selectedChannels)
        for i in indicesToRemove:
            Logger.Info("Hiding channel: %s", validChannels[i])
            AddonSettings.SetChannelVisiblity(validChannels[i], False)
            pass

        for i in indicesToAdd:
            Logger.Info("Showing channel: %s", validChannels[i])
            AddonSettings.SetChannelVisiblity(validChannels[i], True)

        self.Refresh()
        return

    def ShowCountrySettings(self):
        if AddonSettings.IsMinVersion(18):
            AddonSettings.ShowSettings(-99)
        else:
            AddonSettings.ShowSettings(101)
        self.Refresh()

    def ShowSettings(self):
        AddonSettings.ShowSettings()
        self.Refresh()

    def ChannelSettings(self):
        AddonSettings.ShowChannelSettings(self.channelObject)
        self.Refresh()

    def Favourites(self, allFavorites=False):
        # it's just the channel, so only add the favourites
        cmdUrl = self._CreateActionUrl(
            None if allFavorites else self.channelObject,
            action=self.actionAllFavourites if allFavorites else self.actionFavourites
        )

        xbmc.executebuiltin("XBMC.Container.Update({0})".format(cmdUrl))

    @LockWithDialog(logger=Logger.Instance())
    def AddFavourite(self):
        # remove the item
        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        # no need for dates in the favourites
        # item.ClearDate()
        Logger.Debug("Adding favourite: %s", item)

        f = Favourites(Config.favouriteDir)
        if item.IsPlayable():
            action = self.actionPlayVideo
        else:
            action = self.actionListFolder

        # add the favourite
        f.Add(self.channelObject,
              item,
              self._CreateActionUrl(self.channelObject, action, item))

        # we are finished, so just open the Favorites
        self.Favourites()

    @LockWithDialog(logger=Logger.Instance())
    def RemoveFavourite(self):
        # remove the item
        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Debug("Removing favourite: %s", item)
        f = Favourites(Config.favouriteDir)
        f.Remove(item)

        # refresh the list
        self.Refresh()

    def Refresh(self):
        xbmc.executebuiltin("XBMC.Container.Refresh()")
        return

    def ToggleCloak(self):
        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Info("Cloaking current item: %s", item)
        c = Cloaker(self.channelObject, AddonSettings.store(LOCAL), logger=Logger.Instance())

        if c.IsCloaked(item.url):
            c.UnCloak(item.url)
            self.Refresh()
            return

        firstTime = c.Cloak(item.url)
        if firstTime:
            XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.CloakFirstTime),
                                   LanguageHelper.GetLocalizedString(LanguageHelper.CloakMessage))

        del c
        self.Refresh()

    def __GetChannel(self):
        chn = self.params.get(self.keywordChannel, None)
        code = self.params.get(self.keywordChannelCode, None)
        if not chn:
            return None

        Logger.Debug("Fetching channel %s - %s", chn, code)
        channel = ChannelIndex.GetRegister().GetChannel(chn, code, infoOnly=True)
        Logger.Debug("Created channel: %s", channel)
        return channel

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            Logger.Critical("Error in menu handling: %s", exc_val.message, exc_info=True)

        # make sure we leave no references behind
        AddonSettings.ClearCachedAddonSettingsObject()
        # close the log to prevent locking on next call
        Logger.Instance().CloseLog()
        return False

    def SetBitrate(self):
        if self.channelObject is None:
            raise ValueError("Missing channel")

        # taken from the settings.xml
        bitrateOptions = "Retrospect|100|250|500|750|1000|1500|2000|2500|4000|8000|20000".split("|")
        currentBitrate = AddonSettings.GetMaxChannelBitrate(self.channelObject)
        Logger.Debug("Found bitrate for %s: %s", self.channelObject, currentBitrate)
        currentBitrateIndex = 0 if currentBitrate not in bitrateOptions \
            else bitrateOptions.index(currentBitrate)

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.GetLocalizedString(LanguageHelper.BitrateSelection)
        selectedBitrate = dialog.select(heading, bitrateOptions,
                                        preselect=currentBitrateIndex)
        if selectedBitrate < 0:
            return

        Logger.Info("Changing bitrate for %s from %s to %s",
                    self.channelObject,
                    bitrateOptions[currentBitrateIndex],
                    bitrateOptions[selectedBitrate])

        AddonSettings.SetMaxChannelBitrate(self.channelObject, bitrateOptions[selectedBitrate])
        return
