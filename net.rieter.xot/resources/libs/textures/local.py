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

from textures import TextureHandler


class Local(TextureHandler):
    def __init__(self, logger):
        TextureHandler.__init__(self, logger)

    def GetTextureUri(self, channel, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param fileName: the file name
        @param channel:  the channel

        """

        if fileName is None or fileName == "":
            return fileName

        if fileName.startswith("http"):
            self._logger.Trace("Not going to resolve http(s) texture: '%s'.", fileName)
            return fileName

        if os.path.isabs(fileName):
            returnValue = fileName
        else:
            returnValue = os.path.join(channel.path, fileName)

        self._logger.Trace("Resolved texture '%s' to '%s'", fileName, returnValue)
        return returnValue
