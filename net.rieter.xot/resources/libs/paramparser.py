# coding=utf-8
#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import random


from logger import Logger
from pickler import Pickler


class ParameterParser(object):
    def __init__(self, pluginName, params):
        Logger.Debug("Parsing parameters from: %s", params)

        # Url Keywords
        self.keywordPickle = "pickle"                                   # : Used for the pickle item
        self.keywordAction = "action"                                   # : Used for specifying the action
        self.keywordChannel = "channel"                                 # : Used for the channel
        self.keywordChannelCode = "channelcode"                         # : Used for the channelcode
        self.keywordCategory = "category"                               # : Used for the category
        self.keywordRandomLive = "rnd"                                  # : Used for randomizing live items
        self.keywordSettingId = "settingid"                             # : Used for setting an encrypted setting
        self.keywordSettingActionId = "settingactionid"                 # : Used for passing the actionid for the encryption
        self.keywordSettingName = "settingname"                         # : Used for setting an encrypted settings display name
        self.keywordSettingTabFocus = "tabfocus"                        # : Used for setting the tabcontrol to focus after changing a setting
        self.keywordSettingSettingFocus = "settingfocus"                # : Used for setting the setting control to focus after changing a setting
        self.keywordLanguage = "lang"                                   # : Used for the 2 char language information
        self.keywordProxy = "proxy"                                     # : Used so set the proxy index
        self.keywordLocalIP = "localip"                                 # : Used to set the local ip index

        # Url Actions
        self.actionFavourites = "favourites"                            # : Used to show favorites for a channel
        self.actionAllFavourites = "allfavourites"                      # : Used to show all favorites
        self.actionRemoveFavourite = "removefromfavourites"             # : Used to remove items from favorites
        self.actionAddFavourite = "addtofavourites"                     # : Used to add items to favorites
        self.actionDownloadVideo = "downloadVideo"                      # : Used to download a video item
        self.actionPlayVideo = "playvideo"                              # : Used to play a video item
        self.actionUpdateChannels = "updatechannels"                    # : Used to update channels
        self.actionListFolder = "listfolder"                            # : Used to list a folder
        self.actionListCategory = "listcategory"                        # : Used to show the channels from a category
        self.actionConfigureChannel = "configurechannel"                # : Used to configure a channel
        self.actionSetEncryptionPin = "changepin"                       # : Used for setting an application pin
        self.actionSetEncryptedValue = "encryptsetting"                 # : Used for setting an application pin
        self.actionResetVault = "resetvault"                            # : Used for resetting the vault
        self.actionPostLog = "postlog"                                  # : Used for sending log files to pastebin.com
        self.actionProxy = "setproxy"                                   # : Used for setting a proxy

        self.propertyRetrospect = "Retrospect"
        self.propertyRetrospectChannel = "RetrospectChannel"
        self.propertyRetrospectChannelSetting = "RetrospectChannelSettings"
        self.propertyRetrospectFolder = "RetrospectFolder"
        self.propertyRetrospectVideo = "RetrospectVideo"
        self.propertyRetrospectCloaked = "RetrospectCloaked"
        self.propertyRetrospectCategory = "RetrospectCategory"
        self.propertyRetrospectFavorite = "RetrospectFavorite"

        # determine the query parameters
        self.params = self.__GetParameters(params)
        self.pluginName = pluginName

    def _CreateActionUrl(self, channel, action, item=None, category=None):
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
                    Logger.Debug("Adding ChannelCode=None as it was missing from the dict: %s",
                                 result)
                    result[self.keywordChannelCode] = None
            except:
                Logger.Critical("Cannot determine query strings from %s", queryString,
                                exc_info=True)
                raise

        return result
