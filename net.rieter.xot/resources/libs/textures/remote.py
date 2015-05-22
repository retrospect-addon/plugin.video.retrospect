# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import os

from textures import TextureBase


class Remote(TextureBase):
    def __init__(self, cdnUrl, channel, logger):
        TextureBase.__init__(self, channel, logger)

        self.cdnUrl = cdnUrl

        (base, channelName) = os.path.split(self._channel.path)
        (base, addonId) = os.path.split(base)

        if self.cdnUrl:
            self.baseUrl = "%s/%s" % (self.cdnUrl, self._channel.path)
        else:
            self.baseUrl = "http://www.rieter.net/net.rieter.xot.cdn/%s.%s" % (addonId, channelName)

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """

        # all is done by Kodi
        return

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        returnValue =  "%s/%s" % (self.baseUrl, fileName)
        if self._logger is not None:
            self._logger.Trace("Resolved texture '%s' to '%s'", fileName, returnValue)
        return returnValue

