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


def GetTextureHandler(channel, mode="local", logger=None):
    if mode == "local":
        import local
        return local.Local(channel, logger)
    elif mode == "remote":
        import remote
        return remote.Remote(channel, logger)
    elif mode == "package":
        import package
        return package.Package(channel, logger)
    else:
        raise Exception("Invalide mode: %s" % (mode,))


class TextureBase:
    def __init__(self, channel, logger=None):
        self.channel = channel
        self._logger = logger

    def LoadTextureForChannel(self):
        pass

    def GetTextureUri(self, fileName):
        pass