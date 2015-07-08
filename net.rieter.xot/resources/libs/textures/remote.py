# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

from textures import TextureBase


class Remote(TextureBase):
    def __init__(self, cdnUrl, channelPath, logger):
        TextureBase.__init__(self, channelPath, logger, setCdn=True)

        self.cdnUrl = cdnUrl

        if self.cdnUrl:
            self.baseUrl = "%s/%s" % (self.cdnUrl, self._cdnSubFolder)
        else:
            self.baseUrl = "http://www.rieter.net/net.rieter.xot.cdn/%s" % (self._cdnSubFolder, )

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """

        # all is done by Kodi
        return

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        if fileName is None or fileName == "":
            return fileName

        if fileName.startswith("http"):
            returnValue = fileName
        else:
            returnValue = "%s/%s" % (self.baseUrl, fileName)

        self._logger.Trace("Resolved texture '%s' to '%s'", fileName, returnValue)
        return returnValue
