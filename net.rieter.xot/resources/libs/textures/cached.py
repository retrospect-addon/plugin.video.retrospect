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

from textures import TextureBase

class Cached(TextureBase):
    def __init__(self, cdnUrl, cachePath, channel, logger, uriHandler):
        TextureBase.__init__(self, channel, setCdn=True, logger=logger)

        # what is the URL for the CDN?
        self.cdnUrl = cdnUrl
        if self.cdnUrl:
            self.baseUrl = "%s/%s" % (self.cdnUrl, self._cdnSubFolder)
        else:
            self.baseUrl = "http://www.rieter.net/net.rieter.xot.cdn/%s" % (self._cdnSubFolder, )

        self.cachePath = os.path.join(cachePath, "textures", self._cdnSubFolder)
        if not os.path.isdir(self.cachePath):
            os.makedirs(self.cachePath)

        self.__uriHandler = uriHandler

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        # Check if we already have the file
        texturePath = os.path.join(self.cachePath, fileName)
        if not os.path.isfile(texturePath):
            # Missing item. Fetch it
            uri = "%s/%s" % (self.baseUrl, fileName)
            progressBar = lambda retrievedSize, totalSize, perc, completed, status: \
                self._logger.Trace("Downloaded: %s/%s (%s)", retrievedSize, totalSize, perc)

            if self._logger:
                self._logger.Debug("Fetching '%s' from '%s'", fileName, uri)
            texturePath = self.__uriHandler.Download(uri, fileName, os.path.split(texturePath)[0], progressBar)

        return texturePath

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """

        fp = file(os.path.join(self._channelPath, "..", "%s.md5" % (self._addonId, )))
        textures = fp.read()
        fp.close()

        # remove items not in the textures.md5

        # then verify the items that are with the MD5 in the textures.md5
        pass
