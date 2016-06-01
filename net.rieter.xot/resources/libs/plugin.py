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
import random

#import inspect

import xbmcplugin
import xbmc
import xbmcgui

#===============================================================================
# Import XOT stuff
#===============================================================================
try:
    import envcontroller

    #===========================================================================
    # Make global object available
    #===========================================================================
    from logger import Logger
    from addonsettings import AddonSettings
    from locker import LockWithDialog
    from config import Config
    from channelinfo import ChannelInfo
    from xbmcwrapper import XbmcWrapper, XbmcDialogProgressWrapper, XbmcDialogProgressBgWrapper
    from environments import Environments
    from initializer import Initializer
    from updater import Updater
    from favourites import Favourites
    from mediaitem import MediaItem
    from helpers.channelimporter import ChannelIndex
    from helpers.languagehelper import LanguageHelper
    from helpers.htmlentityhelper import HtmlEntityHelper
    from helpers import stopwatch
    from helpers.statistics import Statistics
    from helpers.sessionhelper import SessionHelper
    from textures import TextureHandler
    # from streams.youtube import YouTube
    from pickler import Pickler
    from vault import Vault
except:
    Logger.Critical("Error initializing %s", Config.appName, exc_info=True)


#===============================================================================
# Main Plugin Class
#===============================================================================
class Plugin:
    """Main Plugin Class

    This class makes it possible to access all the XOT channels as a Kodi Add-on
    instead of a script. s

    """

    def __init__(self, pluginName, params, handle=0):
        """Initialises the plugin with given arguments."""

        # some constants
        self.actionDownloadVideo = "downloadVideo".lower()              # : Action used to download a video item
        self.actionFavourites = "favourites".lower()                    # : Action used to show favorites for a channel
        self.actionAllFavourites = "allfavourites".lower()              # : Action used to show all favorites
        self.actionRemoveFavourite = "removefromfavourites".lower()     # : Action used to remove items from favorites
        self.actionAddFavourite = "addtofavourites".lower()             # : Action used to add items to favorites
        self.actionPlayVideo = "playvideo".lower()                      # : Action used to play a video item
        self.actionUpdateChannels = "updatechannels".lower()            # : Action used to update channels
        self.actionListFolder = "listfolder".lower()                    # : Action used to list a folder
        self.actionListCategory = "listcategory"                        # : Action used to show the channels from a category
        self.actionConfigureChannel = "configurechannel"                # : Action used to configure a channel
        self.actionSetEncryptionPin = "setpin"                          # : Action used for setting an application pin
        self.actionSetEncryptedValue = "encryptsetting"                 # : Action used for setting an application pin

        self.keywordPickle = "pickle".lower()                           # : Keyword used for the pickle item
        self.keywordAction = "action".lower()                           # : Keyword used for the action item
        self.keywordChannel = "channel".lower()                         # : Keyword used for the channel
        self.keywordChannelCode = "channelcode".lower()                 # : Keyword used for the channelcode
        self.keywordCategory = "category"                               # : Keyword used for the category
        self.keywordRandomLive = "rnd"                                  # : Keyword used for randomizing live items
        self.keywordSettingId = "settingid"                             # : Keyword used for setting an encrypted setting
        self.keywordSettingName = "settingname"                         # : Keyword used for setting an encrypted settings display name
        self.keywordSettingTabFocus = "tabfocus"                        # : Keyword used for setting the tabcontrol to focus after changing a setting
        self.keywordSettingSettingFocus = "settingfocus"                # : Keyword used for setting the setting control to focus after changing a setting

        self.pluginName = pluginName
        self.handle = int(handle)

        # channel objects
        self.channelObject = None
        self.channelFile = ""
        self.channelCode = None

        self.contentType = "episodes"
        self.methodContainer = dict()   # : storage for the inspect.getmembers(channel) method. Improves performance

        # determine the query parameters
        self.params = self.__GetParameters(params)

        Logger.Info("*********** Starting %s add-on version %s ***********", Config.appName, Config.version)
        Logger.Debug("Plugin Params: %s (%s)\n"
                     "Handle:      %s\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params),
                     self.handle, self.pluginName, params)

        # are we in session?
        sessionActive = SessionHelper.IsSessionActive(Logger.Instance())

        # fetch some environment settings
        envCtrl = envcontroller.EnvController(Logger.Instance())
        # self.FavouritesEnabled = envCtrl.SQLiteEnabled()
        self.FavouritesEnabled = not envCtrl.IsPlatform(Environments.Xbox)

        if not sessionActive:
            # do add-on start stuff
            Logger.Info("Add-On start detected. Performing startup actions.")

            # print the folder structure
            envCtrl.DirectoryPrinter(Config, AddonSettings)

            # show notification
            XbmcWrapper.ShowNotification(None, LanguageHelper.GetLocalizedString(LanguageHelper.StartingAddonId) % (
                Config.appName,), fallback=False, logger=Logger)

            # check for updates
            if envCtrl.IsPlatform(Environments.Xbox):
                Updater().AutoUpdate()

            # check if the repository is available
            envCtrl.IsInstallMethodValid(Config)

            # check for cache folder
            envCtrl.CacheCheck()

            # do some cache cleanup
            envCtrl.CacheCleanUp(Config.cacheDir, Config.cacheValidTime)
            envCtrl.CacheCleanUp(AddonSettings.GetUzgCachePath(), AddonSettings.GetUzgCacheDuration() * 24 * 3600,
                                 "xot.*")

        # create a session
        SessionHelper.CreateSession(Logger.Instance())

        #===============================================================================
        #        Start the plugin version of progwindow
        #===============================================================================
        if len(self.params) == 0:

            # Show initial start if not in a session
            # now show the list
            if AddonSettings.ShowCategories():
                self.ShowCategories()
            else:
                self.ShowChannelList()

        #===============================================================================
        #        Start the plugin verion of the episode window
        #===============================================================================
        else:
            try:
                # Determine what stage we are in. Check that there are more than 2 Parameters
                if len(self.params) > 1 and self.keywordChannel in self.params:
                    # retrieve channel characteristics
                    self.channelFile = os.path.splitext(self.params[self.keywordChannel])[0]
                    self.channelCode = self.params[self.keywordChannelCode]
                    Logger.Debug("Found Channel data in URL: channel='%s', code='%s'", self.channelFile,
                                 self.channelCode)

                    # import the channel
                    channelRegister = ChannelIndex.GetRegister()
                    channel = channelRegister.GetChannel(self.channelFile, self.channelCode)

                    if channel is not None:
                        self.channelObject = channel
                    else:
                        Logger.Critical("None or more than one channels were found, unable to continue.")
                        return

                    # init the channel as plugin
                    self.channelObject.InitChannel()
                    Logger.Info("Loaded: %s", self.channelObject.channelName)

                elif self.keywordCategory in self.params:
                    # no channel needed.
                    pass

                elif self.keywordAction in self.params and (
                        self.params[self.keywordAction] == self.actionAllFavourites or
                        self.params[self.keywordAction] == self.actionRemoveFavourite):
                    # no channel needed for these favourites actions.
                    pass

                elif self.keywordAction in self.params and \
                        self.params[self.keywordAction] == self.actionSetEncryptionPin:
                    try:
                        v = Vault()
                        v.ChangePin()
                    finally:
                        if self.keywordSettingTabFocus in self.params:
                            AddonSettings.ShowSettings(self.params[self.keywordSettingTabFocus],
                                                       self.params.get(self.keywordSettingSettingFocus, None))
                    return

                elif self.keywordAction in self.params and \
                        self.keywordSettingId in self.params and \
                        self.params[self.keywordAction] == self.actionSetEncryptedValue:
                    try:
                        v = Vault()
                        v.SetSetting(self.params[self.keywordSettingId],
                                     self.params.get(self.keywordSettingName, ""))
                        # value = v.GetSetting(self.params[self.keywordSettingId])
                        # Logger.Critical(value)
                    finally:
                        if self.keywordSettingTabFocus in self.params:
                            AddonSettings.ShowSettings(self.params[self.keywordSettingTabFocus],
                                                       self.params.get(self.keywordSettingSettingFocus, None))
                    return
                else:
                    Logger.Critical("Error determining Plugin action")
                    return

                #===============================================================================
                # See what needs to be done.
                #===============================================================================
                if self.keywordAction not in self.params:
                    Logger.Critical("Action parameters missing from request. Parameters=%s", self.params)
                    return

                if self.params[self.keywordAction] == self.actionListCategory:
                    self.ShowChannelList(self.params[self.keywordCategory])

                elif self.params[self.keywordAction] == self.actionConfigureChannel:
                    self.__ConfigureChannel(self.channelObject)

                elif self.params[self.keywordAction] == self.actionFavourites:
                    # we should show the favourites
                    self.ShowFavourites(self.channelObject)

                elif self.params[self.keywordAction] == self.actionAllFavourites:
                    if self.channelObject is not None:
                        Logger.Warning("We have a self.channelObject with self.actionAllFavourites")
                    self.ShowFavourites(None)

                elif self.params[self.keywordAction] == self.actionRemoveFavourite:
                    self.RemoveFavourite()

                elif self.params[self.keywordAction] == self.actionAddFavourite:
                    self.AddFavourite()

                elif self.params[self.keywordAction] == self.actionListFolder:
                    # channelName and URL is present, Parse the folder
                    self.ProcessFolderList()

                elif self.params[self.keywordAction] == self.actionPlayVideo:
                    self.PlayVideoItem()

                elif not self.params[self.keywordAction] == "":
                    self.OnActionFromContextMenu(self.params[self.keywordAction])

                else:
                    Logger.Warning("Number of parameters (%s) or parameter (%s) values not implemented",
                                   len(self.params), self.params)

            except:
                Logger.Critical("Error parsing for add-on", exc_info=True)

        self.__FetchTextures()
        return

    def ShowCategories(self):
        """Displays the ShowCategories that are currently available in XOT as a directory
        listing.
        """

        Logger.Info("Plugin::ShowCategories")
        channelRegister = ChannelIndex.GetRegister()
        categories = channelRegister.GetCategories()

        xbmcItems = []
        icon = os.path.join(Config.rootDir, "icon.png")
        fanart = os.path.join(Config.rootDir, "fanart.jpg")
        for category in categories:
            name = LanguageHelper.GetLocalizedCategory(category)
            xbmcItem = xbmcgui.ListItem(name, name)

            # set art
            try:
                xbmcItem.setIconImage(icon)
            except:
                # it was deprecated
                pass
            xbmcItem.setArt({'thumb': icon, 'icon': icon})
            if not AddonSettings.HideFanart():
                xbmcItem.setArt({'fanart': fanart})

            url = self.__CreateActionUrl(None, action=self.actionListCategory, category=category)
            xbmcItems.append((url, xbmcItem, True))

        # Logger.Trace(xbmcItems)
        ok = xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))
        xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(self.handle, ok)
        return ok

    def ShowChannelList(self, category=None):
        """Displays the channels that are currently available in XOT as a directory
        listing.

        Keyword Arguments:
        category : String - The category to show channels for

        """

        if category:
            Logger.Info("Plugin::ShowChannelList for %s", category)
        else:
            Logger.Info("Plugin::ShowChannelList")
        try:
            # only display channels
            channelRegister = ChannelIndex.GetRegister()
            channels = channelRegister.GetChannels(infoOnly=True)

            xbmcItems = []
            for channel in channels:
                if category and channel.category != category:
                    Logger.Debug("Skipping %s (%s) due to category filter", channel.channelName, channel.category)
                    continue

                # Get the XBMC item
                item = channel.GetXBMCItem()
                # Get the context menu items
                contextMenuItems = self.__GetContextMenuItems(channel)
                item.addContextMenuItems(contextMenuItems)
                # Get the URL for the item
                url = self.__CreateActionUrl(channel, action=self.actionListFolder)

                # Append to the list of XBMC Items
                xbmcItems.append((url, item, True))

            # Add the items
            ok = xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))

            # Just let Kodi display the order we give.
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)
            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            xbmcplugin.endOfDirectory(self.handle, False)
            Logger.Critical("Error fetching channels for plugin", exc_info=True)

    def ShowFavourites(self, channel, replaceExisting=False):
        """ Show the favourites

        Arguments:
        channel : Channel - The channel to show favourites for. Might be None to show all.

        Keyword Arguments:
        replaceExisting : boolean - if True it will replace the current list

        """
        Logger.Debug("Plugin::ShowFavourites")

        if channel is None:
            Logger.Info("Showing all favourites")
        else:
            Logger.Info("Showing favourites for: %s", channel)
        stopWatch = stopwatch.StopWatch("Plugin Favourites timer", Logger.Instance())

        try:
            ok = True
            f = Favourites(Config.favouriteDir)
            favs = f.List(channel)

            # get (actionUrl, pickle) tuples
            # favs = map(lambda (a, p): (a, Pickler.DePickleMediaItem(p)), favs)
            if len(favs) == 0:
                ok = self.__ShowEmptyInformation(favs, favs=True)

            stopWatch.Lap("Items retrieved")

            # create the XBMC items
            xbmcItems = map(lambda item: self.__ConvertMainlistItemToXbmcItem(channel, item[1],
                                                                              True, item[0]), favs)
            stopWatch.Lap("%s items for Kodi generated" % (len(xbmcItems),))

            # add them to XBMC
            ok = ok and xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))
            # add sort handle, but don't use any dates as they make no sense for favourites
            self.__AddSortMethodToHandle(self.handle)

            # set the content
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)
            # make sure we do not cache this one to disc!
            xbmcplugin.endOfDirectory(self.handle, succeeded=ok, updateListing=replaceExisting, cacheToDisc=False)
            stopWatch.Lap("items send to Kodi")

            Logger.Debug("Plugin::Favourites completed. Returned %s item(s)", len(favs))
            stopWatch.Stop()
        except:
            XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.ErrorId),
                                         LanguageHelper.GetLocalizedString(LanguageHelper.ErrorList),
                                         XbmcWrapper.Error, 4000)
            Logger.Error("Plugin::Error parsing favourites", exc_info=True)
            xbmcplugin.endOfDirectory(self.handle, False)

    def ProcessFolderList(self):
        """Wraps the channel.ProcessFolderList"""

        Logger.Info("Plugin::ProcessFolderList Doing ProcessFolderList")
        try:
            ok = True

            selectedItem = None
            if self.keywordPickle in self.params:
                selectedItem = Pickler.DePickleMediaItem(self.params[self.keywordPickle])

            watcher = stopwatch.StopWatch("Plugin ProcessFolderList", Logger.Instance())
            episodeItems = self.channelObject.ProcessFolderList(selectedItem)
            watcher.Lap("Class ProcessFolderList finished")

            if len(episodeItems) == 0:
                Logger.Warning("ProcessFolderList returned %s items", len(episodeItems))
                ok = self.__ShowEmptyInformation(episodeItems)
            else:
                Logger.Debug("ProcessFolderList returned %s items", len(episodeItems))

            xbmcItems = []
            for episodeItem in episodeItems:
                if episodeItem.thumb == "":
                    episodeItem.thumb = self.channelObject.noImage
                if episodeItem.fanart == "":
                    episodeItem.fanart = self.channelObject.fanart

                if episodeItem.type == 'folder' or episodeItem.type == 'append' or episodeItem.type == "page":
                    action = self.actionListFolder
                    folder = True
                elif episodeItem.IsPlayable():
                    action = self.actionPlayVideo
                    folder = False
                else:
                    Logger.Critical("Plugin::ProcessFolderList: Cannot determine what to add")
                    continue

                # Get the XBMC item
                item = episodeItem.GetXBMCItem()
                # Get the context menu items
                contextMenuItems = self.__GetContextMenuItems(self.channelObject, item=episodeItem)
                item.addContextMenuItems(contextMenuItems)
                # Get the action URL
                url = self.__CreateActionUrl(self.channelObject, action=action, item=episodeItem)
                # Add them to the list of XBMC items
                xbmcItems.append((url, item, folder))

            watcher.Lap("Kodi Items generated")
            # add items but if OK was False, keep it like that
            ok = ok and xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))
            watcher.Lap("items send to Kodi")

            if selectedItem is None:
                # mainlist item register channel.
                Statistics.RegisterChannelOpen(self.channelObject, Initializer.StartTime)
                watcher.Lap("Statistics send")

            watcher.Stop()

            self.__AddSortMethodToHandle(self.handle, episodeItems)

            # set the content
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)

            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            Statistics.RegisterError(self.channelObject)
            XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.ErrorId),
                                         LanguageHelper.GetLocalizedString(LanguageHelper.ErrorList),
                                         XbmcWrapper.Error, 4000)
            Logger.Error("Plugin::Error Processing FolderList", exc_info=True)
            xbmcplugin.endOfDirectory(self.handle, False)

    @LockWithDialog(logger=Logger.Instance())
    def RemoveFavourite(self):
        """Removes an item from the favourites"""

        # remove the item
        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Debug("Removing favourite: %s", item)
        f = Favourites(Config.favouriteDir)
        f.Remove(self.channelObject, item)

        # refresh the list
        self.ShowFavourites(self.channelObject, replaceExisting=True)
        pass

    @LockWithDialog(logger=Logger.Instance())
    def AddFavourite(self):
        """Adds an item to the favourites"""

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
              self.__CreateActionUrl(self.channelObject, action, item))

        # we are finished, so just return
        return self.ShowFavourites(self.channelObject)

    @LockWithDialog(logger=Logger.Instance())
    def PlayVideoItem(self):
        """Starts the videoitem using a playlist. """

        Logger.Debug("Playing videoitem using PlayListMethod")

        item = None
        try:
            item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])

            if (item.isDrmProtected or item.isPaid) and AddonSettings.ShowDrmPaidWarning():
                if item.isDrmProtected:
                    Logger.Debug("Showing DRM Warning message")
                    title = LanguageHelper.GetLocalizedString(LanguageHelper.DrmTitle)
                    message = LanguageHelper.GetLocalizedString(LanguageHelper.DrmText)
                    XbmcWrapper.ShowDialog(title, message)
                elif item.isPaid:
                    Logger.Debug("Showing Paid Warning message")
                    title = LanguageHelper.GetLocalizedString(LanguageHelper.PaidTitle)
                    message = LanguageHelper.GetLocalizedString(LanguageHelper.PaidText)
                    XbmcWrapper.ShowDialog(title, message)

            if not item.complete:
                item = self.channelObject.ProcessVideoItem(item)

            # validated the updated item
            if not item.complete or not item.HasMediaItemParts():
                Logger.Warning("UpdateVideoItem returned an item that had item.complete = False:\n%s", item)
                Statistics.RegisterError(self.channelObject, item=item)

            if not item.HasMediaItemParts():
                # the update failed or no items where found. Don't play
                XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.ErrorId),
                                             LanguageHelper.GetLocalizedString(LanguageHelper.NoStreamsId),
                                             XbmcWrapper.Error)
                Logger.Warning("Could not start playback due to missing streams. Item:\n%s", item)
                return

            playData = self.channelObject.PlayVideoItem(item)

            Logger.Debug("Continuing playback in plugin.py")
            if not playData:
                Logger.Warning("PlayVideoItem did not return valid playdata")
                return
            else:
                playList, srt = playData

            # Get the Kodi Player instance (let Kodi decide what player, see
            # http://forum.kodi.tv/showthread.php?tid=173887&pid=1516662#pid1516662)
            xbmcPlayer = xbmc.Player()

            # now we force the busy dialog to close, else the video will not play and the
            # setResolved will not work.
            xbmc.executebuiltin("Dialog.Close(busydialog)")

            resolvedUrl = None
            if item.IsResolvable():
                # now set the resolve to the first URL
                startIndex = playList.getposition()  # the current location
                if startIndex < 0:
                    startIndex = 0
                Logger.Info("Playing stream @ playlist index %s using setResolvedUrl method", startIndex)
                resolvedUrl = playList[startIndex].getfilename()
                xbmcplugin.setResolvedUrl(self.handle, True, playList[startIndex])
            else:
                # playlist do not use the setResolvedUrl
                Logger.Info("Playing stream using Playlist method")
                xbmcPlayer.play(playList)

            # the set the subtitles
            showSubs = AddonSettings.UseSubtitle()
            if srt and (srt != ""):
                Logger.Info("Adding subtitle: %s and setting showSubtitles to %s", srt, showSubs)
                XbmcWrapper.WaitForPlayerToStart(xbmcPlayer, logger=Logger.Instance(), url=resolvedUrl)

                xbmcPlayer.setSubtitles(srt)
                xbmcPlayer.showSubtitles(showSubs)

        except:
            if item:
                Statistics.RegisterError(self.channelObject, item=item)
            else:
                Statistics.RegisterError(self.channelObject)

            XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.ErrorId),
                                         LanguageHelper.GetLocalizedString(LanguageHelper.NoPlaybackId),
                                         XbmcWrapper.Error)
            Logger.Critical("Could not playback the url", exc_info=True)

        return

    def OnActionFromContextMenu(self, action):
        """Peforms the action from a custom contextmenu

        Arguments:
        action : String - The name of the method to call

        """
        Logger.Debug("Performing Custom Contextmenu command: %s", action)

        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        if not item.complete:
            Logger.Debug("The contextmenu action requires a completed item. Updating %s", item)
            item = self.channelObject.ProcessVideoItem(item)

            if not item.complete:
                Logger.Warning("UpdateVideoItem returned an item that had item.complete = False:\n%s", item)

        # invoke
        functionString = "returnItem = self.channelObject.%s(item)" % (action,)
        Logger.Debug("Calling '%s'", functionString)
        try:
            exec functionString
        except:
            Logger.Error("OnActionFromContextMenu :: Cannot execute '%s'.", functionString, exc_info=True)
        return

    def __FetchTextures(self):
        texturesToRetrieve = TextureHandler.Instance().NumberOfMissingTextures()

        if texturesToRetrieve > 0:
            w = None
            try:
                # show a blocking or background progress bar
                if texturesToRetrieve > 4:
                    w = XbmcDialogProgressWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.GetLocalizedString(LanguageHelper.InitChannelTitle)),
                        LanguageHelper.GetLocalizedString(LanguageHelper.FetchTexturesTitle),
                        # Config.TextureUrl
                    )
                else:
                    w = XbmcDialogProgressBgWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.GetLocalizedString(LanguageHelper.FetchTexturesTitle)),
                        Config.TextureUrl
                    )

                bytesTransfered = TextureHandler.Instance().FetchTextures(w.ProgressUpdate)
                if bytesTransfered > 0:
                    Statistics.RegisterCdnBytes(bytesTransfered)
            except:
                Logger.Error("Error fetching textures", exc_info=True)
            finally:
                if w is not None:
                    # always close the progress bar
                    w.Close()
        return

    def __ConfigureChannel(self, channelInfo):
        """ Configures a proxy for a channel

        Arguments:
        channelInfo : ChannelInfo - The channel info

        """

        if not channelInfo:
            Logger.Warning("Cannot configure channel without channel info")

        Logger.Info("Configuring channel: %s", channelInfo)
        AddonSettings.ShowChannelSettings(channelInfo)
        return

    def __ConvertMainlistItemToXbmcItem(self, channel, episodeItem, showFavourites, actionUrl=""):
        Logger.Trace("Converting a mainlist item to XbmcItem with:\nChannel: %s\nItem: %s\nShowFavourites: %s\n"
                     "Actionurl: %s", channel, episodeItem, showFavourites, actionUrl)

        if actionUrl == "" and showFavourites:
            raise Exception("Cannot create favourites XbmcItem without actionUrl")

        item = episodeItem.GetXBMCItem()

        # add the remove from favourites item:
        if showFavourites:
            # XBMC.Container.Refresh refreshes the container and replaces the last history
            # XBMC.Container.Update updates the container and but appends the new list to the history
            contextMenuItems = self.__GetContextMenuItems(channel, item=episodeItem, favouritesList=True)
        else:
            contextMenuItems = self.__GetContextMenuItems(channel, item=episodeItem)

            if self.FavouritesEnabled:
                # add the show favourites here
                cmdUrl = self.__CreateActionUrl(channel, action=self.actionFavourites)
                cmd = "XBMC.Container.Update(%s)" % (cmdUrl,)
                favs = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelFavourites)
                contextMenuItems.append(('Retro: %s' % (favs, ), cmd))

        item.addContextMenuItems(contextMenuItems)

        if actionUrl == "":
            url = self.__CreateActionUrl(channel, self.actionListFolder, item=episodeItem)
        else:
            Logger.Trace("Using predefined actionUrl")
            url = actionUrl

        return url, item, True

    def __AddSortMethodToHandle(self, handle, items=None):
        """ Add a sort method to the plugin output. It takes the Add-On settings into
        account. But if none of the items have a date, it is forced to sort by name.

        Arguments:
        handle : int        - The handle to add the sortmethod to
        items  : MediaItems - The items that need to be sorted

        """

        if AddonSettings.MixFoldersAndVideos():
            labelSortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS
        else:
            labelSortMethod = xbmcplugin.SORT_METHOD_LABEL

        if items:
            hasDates = len(filter(lambda i: i.HasDate(), items)) > 0
            if hasDates:
                Logger.Debug("Sorting method: Dates")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

            hasTracks = len(filter(lambda i: i.HasTrack(), items)) > 0
            if hasTracks:
                Logger.Debug("Sorting method: Tracks")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

        Logger.Debug("Sorting method: Default (Label)")
        xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        return

    def __CreateActionUrl(self, channel, action, item=None, category=None):
        """Creates an URL that includes an action

        Arguments:
        channel : Channel - The channel object to use for the URL
        action  : string  - Action to create an url for

        Keyword Arguments:
        item : MediaItem - The media item to add

        """
        if action is None:
            raise Exception("action is required")

        params = dict()
        if channel:
            params[self.keywordChannel] = channel.moduleName
            if channel.channelCode:
                params[self.keywordChannelCode] = channel.channelCode

        params[self.keywordAction] = action

        # it might have an item or not
        if item is not None:
            params[self.keywordPickle] = Pickler.PickleMediaItem(item)

            if action == self.actionPlayVideo and item.isLive:
                params[self.keywordRandomLive] = random.randint(10000, 99999)

        if category:
            params[self.keywordCategory] = category

        url = "%s?" % (self.pluginName, )
        for k in params.keys():
            url = "%s%s=%s&" % (url, k, params[k])

        url = url.strip('&')
        # Logger.Trace("Created url: '%s'", url)
        return url

    def __GetContextMenuItems(self, channel, item=None, favouritesList=False):
        """Retrieves the context menu items to display

        Arguments:
        channel : Channel - The channel from which to get the context menu items. The channel might be None in case of
                            some actions that do not require a channel.

        Keyword Arguments
        item           : MediaItem - The item to which the context menu belongs.
        favouritesList : Boolean   - Indication that the menu is for the favorites
        """

        contextMenuItems = []

        favs = LanguageHelper.GetLocalizedString(LanguageHelper.FavouritesId)
        allFavs = LanguageHelper.GetLocalizedString(LanguageHelper.AllFavouritesId)

        # let's put this one on top
        if item is not None:
            # add a default enqueue list
            cmd = "XBMC.Action(Queue)"
            enqueue = LanguageHelper.GetLocalizedString(LanguageHelper.QueueItemId)
            contextMenuItems.append(("%s" % (enqueue,), cmd))

        cmdUrl = self.__CreateActionUrl(channel, action=self.actionConfigureChannel)
        cmd = "XBMC.RunPlugin(%s)" % (cmdUrl,)
        Logger.Trace("Adding command: %s", cmd)
        title = LanguageHelper.GetLocalizedString(LanguageHelper.ShowChannelSettings)
        contextMenuItems.append(("Retro: %s" % (title, ), cmd))

        if item is None:
            if self.FavouritesEnabled:
                # it's just the channel, so only add the favourites
                cmdUrl = self.__CreateActionUrl(channel, action=self.actionFavourites)
                cmd = "XBMC.Container.Update(%s)" % (cmdUrl,)
                # Logger.Trace("Adding command: %s", cmd)
                channelFavs = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelFavourites)
                contextMenuItems.append(("Retro: %s" % (channelFavs,), cmd))

                cmdUrl = self.__CreateActionUrl(None, action=self.actionAllFavourites)
                cmd = "XBMC.Container.Update(%s)" % (cmdUrl,)
                Logger.Trace("Adding command: %s", cmd)
                contextMenuItems.append(("Retro: %s" % (allFavs, ), cmd))

            return contextMenuItems

        # add a default refresh list
        cmd = "XBMC.Container.Refresh()"
        refresh = LanguageHelper.GetLocalizedString(LanguageHelper.RefreshListId)
        contextMenuItems.append(("Retro: %s" % (refresh,), cmd))

        # we have an item
        if favouritesList:
            # we have list of favourites
            cmdUrl = self.__CreateActionUrl(channel, action=self.actionRemoveFavourite, item=item)
            cmd = "XBMC.Container.Update(%s)" % (cmdUrl,)
            # Logger.Trace("Adding command: %s", cmd)

            remove = LanguageHelper.GetLocalizedString(LanguageHelper.RemoveId)
            fav = LanguageHelper.GetLocalizedString(LanguageHelper.FavouriteId)
            contextMenuItems.append(("Retro: %s %s" % (remove, fav), cmd))

        elif item.type == "folder" and self.FavouritesEnabled:
            # we need to run RunPlugin here instead of Refresh as we don't want to refresh any lists
            # the refreshing results in empty lists in XBMC4Xbox.
            cmdUrl = self.__CreateActionUrl(channel, action=self.actionAddFavourite, item=item)
            # cmd = "XBMC.RunPlugin(%s)" % (cmdUrl,)
            cmd = "XBMC.Container.Update(%s)" % (cmdUrl,)
            # Logger.Trace("Adding command: %s", cmd)
            addTo = LanguageHelper.GetLocalizedString(LanguageHelper.AddToId)
            contextMenuItems.append(("Retro: %s %s" % (addTo, favs), cmd))

        # if it was a favourites list, don't add the channel methods as they might be from a different channel
        if channel is None:
            return contextMenuItems

        # now we process the other items
        possibleMethods = self.__GetMembers(channel)
        # Logger.Debug(possibleMethods)

        for menuItem in channel.contextMenuItems:
            # Logger.Debug(menuItem)
            if menuItem.itemTypes is None or item.type in menuItem.itemTypes:
                # We don't care for complete here!
                # if menuItem.completeStatus == None or menuItem.completeStatus == item.complete:

                # see if the method is available
                methodAvailable = False

                for method in possibleMethods:
                    if method == menuItem.functionName:
                        methodAvailable = True
                        # break from the method loop
                        break

                if not methodAvailable:
                    Logger.Warning("No method for: %s", menuItem)
                    continue

                cmdUrl = self.__CreateActionUrl(channel, action=menuItem.functionName, item=item)
                cmd = "XBMC.RunPlugin(%s)" % (cmdUrl,)
                title = "Retro: %s" % (menuItem.label,)
                Logger.Trace("Adding command: %s | %s", title, cmd)
                contextMenuItems.append((title, cmd))

        return contextMenuItems

    def __GetMembers(self, channel):
        """ Caches the inspect.getmembers(channel) method for performance
        matters

        """

        if channel.guid not in self.methodContainer:
            #self.methodContainer[channel.guid] = inspect.getmembers(channel)
            self.methodContainer[channel.guid] = dir(channel)

        return self.methodContainer[channel.guid]

    def __GetParameters(self, queryString):
        """ Extracts the actual parameters as a dictionary from the passed in
        querystring. This method takes the self.quotedPlus into account.

        Arguments:
        queryString : String - The querystring

        Returns:
        dict() of keywords and values.

        """
        result = dict()
        queryString = queryString.strip('?')
        if queryString != '':
            try:
                for pair in queryString.split("&"):
                    (k, v) = pair.split("=")
                    result[k] = v

                # if the channelcode was empty, it was stripped, add it again.
                if self.keywordChannelCode not in result:
                    Logger.Debug("Adding ChannelCode=None as it was missing from the dict: %s", result)
                    result[self.keywordChannelCode] = None
            except:
                Logger.Critical("Cannot determine query strings from %s", queryString, exc_info=True)
                raise

        return result

    def __ShowEmptyInformation(self, items, favs=False):
        """ Adds an empty item to a list or just shows a message.
        @type favs: boolean indicating that we are dealing with favourites
        @param items: the list of items

        @rtype : boolean indicating succes or not

        """

        if self.channelObject:
            Statistics.RegisterError(self.channelObject)

        if favs:
            title = LanguageHelper.GetLocalizedString(LanguageHelper.NoFavsId)
        else:
            title = LanguageHelper.GetLocalizedString(LanguageHelper.ErrorNoEpisodes)

        behaviour = AddonSettings.GetEmptyListBehaviour()

        Logger.Debug("Showing empty info for mode (favs=%s): [%s]", favs, behaviour)
        if behaviour == "error":
            # show error
            ok = False
        elif behaviour == "dummy" and not favs:
            # We should add a dummy items, but not for favs
            emptyListItem = MediaItem("- %s -" % (title.strip("."), ), "", type='video')
            emptyListItem.icon = self.channelObject.icon
            emptyListItem.thumb = self.channelObject.noImage
            emptyListItem.fanart = self.channelObject.fanart
            emptyListItem.dontGroup = True
            emptyListItem.description = "This listing was left empty intentionally."
            emptyListItem.complete = True
            emptyListItem.fanart = self.channelObject.fanart
            # add funny stream here?
            # part = emptyListItem.CreateNewEmptyMediaPart()
            # for s, b in YouTube.GetStreamsFromYouTube("", self.channelObject.proxy):
            #     part.AppendMediaStream(s, b)

            # if we add one, set OK to True
            ok = True
            items.append(emptyListItem)
        else:
            ok = True

        XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.ErrorId),
                                     title, XbmcWrapper.Error, 2500)
        return ok
