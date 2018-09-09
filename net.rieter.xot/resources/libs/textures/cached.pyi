from typing import Any, Dict

from channelinfo import ChannelInfo
from textures import TextureHandler
from logger import Logger
from urihandler import _RequestsHandler


# noinspection PyMissingConstructor
class Cached(TextureHandler):
    __channelTextureUri = ...  # type: str
    __channelTexturePath = ...  # type: str
    __cdnUrl = ...  # type: str
    __textureQueue = ...  # type: Dict[str, str]
    __uriHandler = ... # type: _RequestsHandler

    def __init__(self, cdnUrl: str, cachePath: str, cacheUri: str, logger: Logger, uriHandler: Any) -> None: ...

    def GetTextureUri(self, channel: ChannelInfo, fileName: str) -> str: ...

    def NumberOfMissingTextures(self) -> int: ...

    def FetchTextures(self, dialogCallBack: Any=None) -> int: ...

    def PurgeTextureCache(self, channel: Any) -> None: ...

    def __FetchTexture(self, uri: str, texturePath: str) -> int: ...

    def __GetHash(self, filePath: str) -> str: ...
