# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

from textures import TextureHandler


class Remote(TextureHandler):
    def __init__(self, cdnUrl, logger):
        TextureHandler.__init__(self, logger)

        self.__cdnUrl = cdnUrl
        if not self.__cdnUrl:
            self.__cdnUrl = "http://www.rieter.net/net.rieter.xot.cdn/"

    def PurgeTextureCache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        @param channel:  the channel

        """

        cdnFolder = self._GetCdnSubFolder(channel)
        self._logger.Info("Purging Kodi Texture for: %s", cdnFolder)
        self._PurgeXbmcCache(cdnFolder)
        return

    def GetTextureUri(self, channel, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param fileName: the file name
        @param channel:  the channel

        """

        if fileName is None or fileName == "":
            return fileName

        if fileName.startswith("http"):
            returnValue = fileName
        else:
            cdnFolder = self._GetCdnSubFolder(channel)
            returnValue = "%s/%s/%s" % (self.__cdnUrl, cdnFolder, fileName)

        self._logger.Debug("Resolved texture '%s' to '%s'", fileName, returnValue)
        return returnValue
