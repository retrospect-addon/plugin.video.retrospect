#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
__all__ = ["local", "remote", "package"]

import os

Local = "local"
Remote = "remote"
Cached = "cached"


def GetTextureHandler(channel, config, uriHandler=None, logger=None):
    """ Fetches a TextureManager for specific mode and channel.

    @param channel:             The Channel or ChannelInfo object
    @param config:              The Retrospect Config object
    @param uriHandler:          The UriHandler
    @param logger:              An optional Logger

    @return: A TextureBase object for the requested mode

    """

    mode = config.TextureMode.lower()
    if logger is not None:
        logger.Trace("Creating '%s' Texture Mananger for: %s", mode, channel)

    if mode == Local:
        import local
        return local.Local(channel.path, logger)
    elif mode == Remote:
        import remote
        return remote.Remote(config.TextureUrl, channel.path, logger)
    elif mode == Cached:
        import cached
        return cached.Cached(config.TextureUrl, config.profileDir, channel.path, logger, uriHandler)
    else:
        raise Exception("Invalide mode: %s" % (mode,))


class TextureBase:
    def __init__(self, channelPath, setCdn=False, logger=None):
        """ Initialize the texture base

        @param channelPath: The local path where the corresponding channel is
        @param setCdn:      Indicator if the determine CDN variables (performance impact)
        @param logger:      You can add a logger if you want.

        """

        self._channelPath = channelPath
        self._logger = logger
        self._addonId = None
        self._cdnSubFolder = None

        if setCdn:
            (base, channelName) = os.path.split(self._channelPath)
            (base, addonId) = os.path.split(base)
            self._addonId = addonId
            # self._channelName = channel.channelName
            self._cdnSubFolder = "%s.%s" % (addonId, channelName)

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """
        pass

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """
        pass
