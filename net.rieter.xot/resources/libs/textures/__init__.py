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
from xbmcwrapper import XbmcWrapper
from helpers.jsonhelper import JsonHelper

__all__ = ["local", "remote", "cached", "TextureHandler"]

Local = "local"
Remote = "remote"
Cached = "cached"


class TextureHandler:
    __TextureHandler = None

    def __init__(self, logger):
        """ Initialize the texture base

        @param logger:      A logger to log stuff.

        """

        self._logger = logger               # : a logger
        self._addonId = None                # : the addon ID

        # some dictionaries for caching
        self.__cdnPaths = {}
        self.__addonIds = {}

    @staticmethod
    def Instance():
        return TextureHandler.__TextureHandler

    @staticmethod
    def SetTextureHandler(config, logger, uriHandler=None):
        """ Fetches a TextureManager for specific mode and channel.

        @param config:              The Retrospect Config object
        @param logger:              An Logger
        @param uriHandler:          The UriHandler

        @return: A TextureHandler object for the requested mode

        """

        mode = config.TextureMode.lower()
        if logger is not None:
            logger.Trace("Creating '%s' Texture Mananger", mode)

        if mode == Local:
            import local
            TextureHandler.__TextureHandler = local.Local(logger)
        elif mode == Remote:
            import remote
            TextureHandler.__TextureHandler = remote.Remote(config.TextureUrl, logger)
        elif mode == Cached:
            import cached
            TextureHandler.__TextureHandler = cached.Cached(config.TextureUrl,
                                                            config.profileDir, config.profileUri,
                                                            logger, uriHandler)
        else:
            raise Exception("Invalide mode: %s" % (mode,))

        return TextureHandler.__TextureHandler

    def GetTextureUri(self, channel, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param fileName: the file name
        @param channel:  the channel

        """

        # Should be implemented
        pass

    def NumberOfMissingTextures(self):
        """ Indication whether or not textures need to be retrieved.

        @return: a boolean value
        """

        # Could be implemented
        return 0

    def FetchTextures(self, dialogCallBack=None):
        """ Fetches all the needed textures

        @param dialogCallBack:  Callback method with signature
                                Function(self, retrievedSize, totalSize, perc, completed, status)

        @return: the number of bytes fetched

        """

        # Could be implemented
        return 0

    def PurgeTextureCache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        @param channel:  the channel

        """

        # Should be implemented
        pass

    def _GetAddonId(self, channel):
        """ Determines the add-on ID from the add-on to which the channel belongs,
        e.g.: net.rieter.xot.channel.be

        @param channel: the channel to determine the CDN folder for.

        Remark: we cache some stuff for performance improvements

        """

        if channel.path in self.__addonIds:
            return self.__addonIds[channel.path]

        parts = channel.path.rsplit(os.sep, 2)[-2:]
        addonId = parts[0]
        self.__addonIds[channel.path] = addonId
        return addonId

    def _GetCdnSubFolder(self, channel):
        """ Determines the CDN folder, e.g.: net.rieter.xot.channel.be.canvas

        @param channel: the channel to determine the CDN folder for.

        Remark: we cache some stuff for performance improvements

        """

        if channel.path in self.__cdnPaths:
            return self.__cdnPaths[channel.path]

        parts = channel.path.rsplit(os.sep, 2)[-2:]
        cdn = ".".join(parts)
        self.__cdnPaths[channel.path] = cdn
        return cdn

    def _PurgeXbmcCache(self, channelTexturePath):
        """ Class the JSON RPC within Kodi that removes all changed items which paths contain the
        value given in channelTexturePath

        @param channelTexturePath: string - The

        """

        jsonCmd = '{' \
                  '"jsonrpc": "2.0", ' \
                  '"method": "Textures.GetTextures", ' \
                  '"params": {' \
                  '"filter": {"operator": "contains", "field": "url", "value": "%s"}, ' \
                  '"properties": ["url"]' \
                  '}, ' \
                  '"id": "libTextures"' \
                  '}' % (channelTexturePath, )
        jsonResults = XbmcWrapper.ExecuteJsonRpc(jsonCmd, self._logger)

        results = JsonHelper(jsonResults, logger=self._logger)
        if "error" in results.json or "result" not in results.json:
            self._logger.Error("Error retreiving textures:\nCmd   : %s\nResult: %s", jsonCmd, results.json)
            return

        results = results.GetValue("result", "textures", fallback=[])
        for result in results:
            textureId = result["textureid"]
            textureUrl = result["url"]
            self._logger.Debug("Going to remove texture: %d - %s", textureId, textureUrl)
            jsonCmd = '{' \
                      '"jsonrpc": "2.0", ' \
                      '"method": "Textures.RemoveTexture", ' \
                      '"params": {' \
                      '"textureid": %s' \
                      '}' \
                      '}' % (textureId,)
            XbmcWrapper.ExecuteJsonRpc(jsonCmd, self._logger)
        return
