# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.backtothefuture import PY2
if PY2:
    # noinspection PyPep8Naming,PyUnresolvedReferences
    import cPickle as pickle
else:
    import pickle

import os
import io
import sys
import base64
from functools import reduce

from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem


class Pickler:
    # hack for Base64 chars that are URL encoded. We only need 3 (or 6 to make it case-insenstive)
    # and then we don't need to use urlencode which is slow in Python.
    __Base64CharsDecode = {
        "-": "\n",
        "%3d": "=",
        "%3D": "=",
        "%2f": "/",
        "%2F": "/",
        "%2b": "+",
        "%2B": "+"
    }
    __Base64CharsEncode = {
        "\n": "-",
        "=": "%3d",
        "/": "%2f",
        "+": "%2b",
    }

    def __init__(self, pickle_store_path=None):
        # store some vars for speed optimization
        self.__pickleContainer = dict()  # : storage for pickled items to prevent duplicate pickling
        self.__pickle_store_path = pickle_store_path
        self.__gzip = True

    def de_pickle_media_item(self, hex_string):
        """ De-serializes a serialized mediaitem.

        Warning: Pickling from Python2 to Python3 will not work.

        :param str|unicode hex_string: Base64 encoded string that should be decoded.

        :return: The object that was Pickled and Base64 encoded.

        """

        if "--" in hex_string:
            return self.__retrieve_media_item_from_store(hex_string)

        # In order to not break any already pickled objects, we need to make sure that we have
        if "mediaitem" not in sys.modules:
            import resources.lib.mediaitem
            sys.modules['mediaitem'] = resources.lib.mediaitem

        hex_string = hex_string.rstrip(' ')
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsDecode[y]),
                            Pickler.__Base64CharsDecode.keys(),
                            hex_string)

        Logger.trace("DePickle: HexString: %s (might be truncated)", hex_string[0:256])

        pickle_string = base64.b64decode(hex_string)  # type: bytes
        pickle_item = pickle.loads(pickle_string)  # type: object
        return pickle_item

    def pickle_media_item(self, item):
        """ Serialises a mediaitem using Pickle

        :param Any item: The item that should be serialized
        :return: A pickled and Base64 encoded serialization of the `item`.
        :rtype: str

        """

        if item.guid in self.__pickleContainer:
            Logger.trace("Pickle Container cache hit: %s", item.guid)
            return self.__pickleContainer[item.guid]

        pickle_string = pickle.dumps(item, protocol=pickle.HIGHEST_PROTOCOL)  # type: bytes
        hex_bytes = base64.b64encode(pickle_string)  # type: bytes
        hex_string = hex_bytes.decode()  # type: str

        # if not unquoted, we must replace the \n's for the URL
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsEncode[y]),
                            Pickler.__Base64CharsEncode.keys(),
                            hex_string)

        self.__pickleContainer[item.guid] = hex_string
        return hex_string

    def validate(self, test, raise_on_missing=False, logger=None):
        """ Validates if in instance has all properties after depickling. The __class__ of
        the 'test' should implement a self.__dir__(self) that returns the required attributes.

        :param any test:                Item to test
        :param bool raise_on_missing:   If True an error will be raised on failure
        :param Logger|None logger:      Pass a loger in

        :return: None if no error, or an error message if an error occurred.
        :rtype: str|None

        """

        if logger is not None:
            Logger.trace("Testing: %s", test.__dir__())

        # the default dir() does not work for Android at the moment.
        for attribute in test.__dir__():
            if logger is not None:
                logger.trace("Testing: %s", attribute)

            # manage private attributes
            if attribute.startswith("__"):
                attribute = "_%s%s" % (test.__class__.__name__, attribute)

            if not hasattr(test, attribute):
                error = "Attribute Missing: %s" % attribute

                if logger is not None:
                    logger.warning(error)
                if raise_on_missing:
                    raise Exception(error)
                return error

        # We are good
        return None

    def purge_store(self, age=30):
        """ Purges all files older than xx days.

        :param int age:     The age (in days) for pickles to be purged

        """

        if self.__pickle_store_path is None:
            return

        import glob
        import time
        Logger.info("PickleStore: purging store items older than %d days", age)

        pickles_path = os.path.join(self.__pickle_store_path, "pickles", "*", "*", "*.store.gz")
        cache_time = age * 30 * 24 * 60 * 60
        for filename in glob.glob(pickles_path):
            create_time = os.path.getctime(filename)
            if create_time + cache_time < time.time():
                os.remove(filename)
                Logger.debug("PickleStore: Removed file '%s'", filename)

    def store_media_items(self, store_guid, parent, children):
        """ Store the MediaItems in the given store path

        :param str store_guid:              The guid used for storage
        :param MediaItem parent:            The parent item
        :param list[MediaItem] children:    The child items

        :rtype: str

        """

        if self.__pickle_store_path is None:
            raise ValueError("Cannot find pickle store path")

        if store_guid is None:
            raise ValueError("No parent and not channel guid specified")

        children = children or []

        # The path is constructed like this for abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx:
        # <storepath>/ab/cd/abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        pickles_dir, pickles_path = self.__get_pickle_path(store_guid)
        Logger.debug("PickleStore: write to '%s'", pickles_path)

        if not os.path.isdir(pickles_dir):
            os.makedirs(pickles_dir)

        content = {
            "parent": parent,
            "children": {item.guid: item for item in children}
        }

        if not self.__gzip:
            with io.open(pickles_path, "wb+") as fp:
                pickle.dump(content, fp, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            import gzip
            with gzip.GzipFile(pickles_path, 'wb+') as fp:
                fp.write(pickle.dumps(content, protocol=pickle.HIGHEST_PROTOCOL))

        return

    def __retrieve_media_item_from_store(self, storage_location):
        store_guid, item_guid = storage_location.split("--")
        pickles_dir, pickles_path = self.__get_pickle_path(store_guid)
        Logger.debug("PickleStore: reading %s from '%s'", item_guid, pickles_path)

        try:
            if self.__gzip:
                import gzip
                with gzip.GzipFile(pickles_path, "rb") as fp:
                    pickle_bytes = fp.read()
                    content = pickle.loads(pickle_bytes)
            else:
                with io.open(pickles_path, "rb") as fp:
                    content = pickle.load(fp)
        except:
            Logger.error("Error opening '%s'", pickles_path, exc_info=True)
            return None

        items = content.get("children")
        item_pickle = items.get(item_guid)
        return item_pickle

    def __get_pickle_path(self, store_guid):
        # file storage is always lower case
        store_guid = store_guid.lower()

        if self.__gzip:
            pickles_file = "{}.store.gz".format(store_guid)
        else:
            pickles_file = "{}.store".format(store_guid)

        pickles_dir = os.path.join(
            self.__pickle_store_path, "pickles", store_guid[0:2], store_guid[2:4])
        pickles_path = os.path.join(pickles_dir, pickles_file)
        return pickles_dir, pickles_path
