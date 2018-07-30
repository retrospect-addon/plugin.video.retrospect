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
import io
import datetime
from .filecache import LockedReadWrite


class StreamCache(object):
    def __init__(self, cachePath):
        self.cacheHits = 0
        self.cachePath = os.path.join(cachePath, "www")
        if not os.path.isdir(self.cachePath):
            os.makedirs(self.cachePath)

    @LockedReadWrite
    def set(self, key):
        file_name = os.path.join(self.cachePath, key)
        fp = io.open(file_name, mode="w+b")
        return fp

    @LockedReadWrite
    def get(self, key):
        file_name = os.path.join(self.cachePath, key)
        with io.open(file_name, mode="rb") as fp:
            return io.BytesIO(fp.read())

    def is_expired(self, key, seconds=3600):
        file_name = os.path.join(self.cachePath, key)
        if not os.path.isfile(file_name):
            return False

        storeTime = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
        validUntil = storeTime + datetime.timedelta(seconds=seconds)
        if validUntil < datetime.datetime.now():
            return True

        return False

    def has_key(self, key):
        """ Returns if a key is present (expired or not) in the cache.

        Arguments:
        key     : String  - The key to use to check the cache values

        Returns True or False

        """

        file_name = os.path.join(self.cachePath, key)
        return os.path.isfile(file_name)

    def __str__(self):
        return "Cache store [{0}]".format(self.cachePath)
