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

from logger import Logger


class ParameterParser(object):
    def __init__(self, pluginName, params):
        Logger.Debug("Parsing parameters from: %s", params)

        self.keywordPickle = "pickle".lower()  # : Keyword used for the pickle item
        self.keywordAction = "action".lower()  # : Keyword used for the action item
        self.keywordChannel = "channel".lower()  # : Keyword used for the channel
        self.keywordChannelCode = "channelcode".lower()  # : Keyword used for the channelcode
        self.keywordCategory = "category"  # : Keyword used for the category
        self.keywordRandomLive = "rnd"  # : Keyword used for randomizing live items
        self.keywordSettingId = "settingid"  # : Keyword used for setting an encrypted setting
        self.keywordSettingActionId = "settingactionid"  # : Keyword used for passing the actionid for the encryption
        self.keywordSettingName = "settingname"  # : Keyword used for setting an encrypted settings display name
        self.keywordSettingTabFocus = "tabfocus"  # : Keyword used for setting the tabcontrol to focus after changing a setting
        self.keywordSettingSettingFocus = "settingfocus"  # : Keyword used for setting the setting control to focus after changing a setting
        self.keywordLanguage = "lang"  # : Keyword used for the 2 char language information
        self.keywordProxy = "proxy"  # : Keyword used so set the proxy index
        self.keywordLocalIP = "localip"  # : Keyword used to set the local ip index

        # determine the query parameters
        self.params = self.__GetParameters(params)
        self.pluginName = pluginName

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
