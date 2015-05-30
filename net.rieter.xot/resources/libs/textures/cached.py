#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import hashlib
import os

from textures import TextureBase
from xbmcwrapper import XbmcWrapper
from helpers.jsonhelper import JsonHelper


class Cached(TextureBase):
    def __init__(self, textureUrl, cachePath, channel, logger, uriHandler):
        TextureBase.__init__(self, channel, logger, setCdn=True)

        # what is the URL for the CDN?
        if textureUrl:
            self.__channelTextureUrl = "%s/%s" % (textureUrl, self._cdnSubFolder)
        else:
            self.__channelTextureUrl = "http://www.rieter.net/net.rieter.xot.cdn/%s" % (self._cdnSubFolder, )

        self.__channelTexturePath = os.path.join(cachePath, "textures", self._cdnSubFolder)
        if not os.path.isdir(self.__channelTexturePath):
            os.makedirs(self.__channelTexturePath)

        self.__uriHandler = uriHandler

        # we should keep track of which ones we already used in this session, so we can refetch it in a purge situation.
        self.__retrievedTexturePaths = []

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """

        if os.path.isabs(fileName):
            self._logger.Trace("Already cached texture found: '%s'", fileName)
            return fileName

        # Check if we already have the file
        texturePath = os.path.join(self.__channelTexturePath, fileName)
        if not os.path.isfile(texturePath):
            # Missing item. Fetch it
            uri = "%s/%s" % (self.__channelTextureUrl, fileName)
            self._logger.Trace("Fetching texture '%s' from '%s'", fileName, uri)

            imageBytes = self.__uriHandler.Open(uri)
            if imageBytes:
                fs = open(texturePath, mode='wb')
                fs.write(imageBytes)
                fs.close()
            else:
                # fallback to local cache.
                texturePath = os.path.join(self._channelPath, fileName)

                self._logger.Error("Could not update Texture: %s. Falling back to: %s", uri, texturePath)

        self._logger.Trace("Returning cached texture for '%s' from '%s'", fileName, texturePath)
        self.__retrievedTexturePaths.append(texturePath)
        return texturePath

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """

        self._logger.Info("Purging Texture for: %s", self._channelPath)

        # read the md5 hashes
        fp = file(os.path.join(self._channelPath, "..", "%s.md5" % (self._addonId, )))
        lines = fp.readlines()
        fp.close()

        # get a lookup table
        textures = [reversed(line.rstrip().split(" ")) for line in lines]
        # noinspection PyTypeChecker
        textures = dict(textures)

        # remove items not in the textures.md5
        images = [image for image in os.listdir(self.__channelTexturePath)
                  if image.lower().endswith(".png") or image.lower().endswith(".png")]

        for image in images:
            imageKey = "%s/%s" % (self._cdnSubFolder, image)
            filePath = os.path.join(self.__channelTexturePath, image)

            if imageKey in textures:
                # verify the MD5 in the textures.md5
                md5 = self.__GetHash(filePath)
                if md5 == textures[imageKey]:
                    self._logger.Trace("Texture up to date: %s", filePath)
                else:
                    self._logger.Warning("Texture expired: %s", filePath)
                    os.remove(filePath)

                    # and fetch the updated one if it was already used
                    if filePath in self.__retrievedTexturePaths:
                        self.GetTextureUri(image)
            else:
                self._logger.Warning("Texture no longer required: %s", filePath)
                os.remove(filePath)

        # always reset the Kodi Texture cache for this channel
        self.__PurgeXbmcCache(self.__channelTexturePath)
        return

    def __GetHash(self, filePath):
        hashObject = hashlib.md5()
        with open(filePath, "rb") as fs:
            for block in iter(lambda: fs.read(65536), ""):
                hashObject.update(block)
        md5 = hashObject.hexdigest()
        return md5

    def __PurgeXbmcCache(self, channelTexturePath):
        jsonCmd = '{' \
                  '"jsonrpc": "2.0", ' \
                  '"method": "Textures.GetTextures", ' \
                  '"params": {' \
                  '"filter": {"operator": "contains", "field": "url", "value": "%s"}, ' \
                  '"properties": ["url"]' \
                  '}, ' \
                  '"id": "libTextures"' \
                  '}' % \
                  (os.path.split(channelTexturePath)[-1], )
        jsonResults = XbmcWrapper.ExecuteJsonRpc(jsonCmd, self._logger)

        results = JsonHelper(jsonResults, logger=self._logger)
        if "error" in results.json or "result" not in results.json:
            self._logger.Error("Error retreiving textures:\nCmd   : %s\nResult: %s", jsonCmd, results.json)
            return

        results = results.GetValue("result", "textures")
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
