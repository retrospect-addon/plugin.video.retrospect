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


def GetTextureHandler(channel, config, logger, uriHandler=None):
    """ Fetches a TextureManager for specific mode and channel.

    @param channel:             The Channel or ChannelInfo object
    @param config:              The Retrospect Config object
    @param logger:              An Logger
    @param uriHandler:          The UriHandler

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
    _bytesTransfered = 0                    # : the bytes transfered

    def __init__(self, channelPath, logger, setCdn=False):
        """ Initialize the texture base

        @param channelPath: The local path where the corresponding channel is
        @param setCdn:      Indicator if the determine CDN variables (performance impact)
        @param logger:      A logger to log stuff.

        """

        self._channelPath = channelPath     # : the path of the actual channel
        self._logger = logger               # : a logger
        self._addonId = None                # : the addon ID
        self._cdnSubFolder = None           # : the subfolder for the CDN

        if setCdn:
            (base, channelName) = os.path.split(self._channelPath)
            (base, addonId) = os.path.split(base)
            self._addonId = addonId
            # self._channelName = channel.channelName
            self._cdnSubFolder = "%s.%s" % (addonId, channelName)

    @staticmethod
    def GetBytesTransfered():
        """
        @return: the total number of bytes transfered so far.
        """

        return TextureBase._bytesTransfered

    def GetTextureUri(self, fileName):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @type fileName: the file name

        """
        pass

    def PurgeTextureCache(self):
        """ Removes those entries from the textures cache that are no longer required. """
        pass
