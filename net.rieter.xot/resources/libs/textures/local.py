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
from fileinput import filename

from textures import TextureBase


class Local(TextureBase):
    def __init__(self, channelPath, logger):
        TextureBase.__init__(self, channelPath, logger)

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        if fileName is None or fileName == "":
            return fileName

        if fileName.startswith("http"):
            self._logger.Trace("Not going to resolve http(s) texture: '%s'.", fileName)
            return fileName

        if os.path.isabs(fileName):
            returnValue = fileName
        else:
            returnValue = os.path.join(self._channelPath, fileName)

        self._logger.Trace("Resolved texture '%s' to '%s'", fileName, returnValue)
        return returnValue
