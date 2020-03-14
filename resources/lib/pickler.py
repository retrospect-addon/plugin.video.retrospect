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
from resources.lib.helpers.jsonhelper import JsonHelper


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

    def __init__(self):
        # store some vars for speed optimization
        self.__pickleContainer = dict()  # : storage for pickled items to prevent duplicate pickling

    def de_pickle_media_item(self, hex_string):
        """ De-serializes a serialized mediaitem.

        Warning: Pickling from Python2 to Python3 will not work.

        :param str|unicode hex_string: Base64 encoded string that should be decoded.

        :return: The object that was Pickled and Base64 encoded.

        """

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

    def store_media_items(self, store_path, parent, children, channel_guid=None):
        """ Store the MediaItems in the given store path

        :param str store_path:              The path where to store it
        :param MediaItem parent:            The parent item
        :param list[MediaItem] children:    The child items
        :param str channel_guid:            The guid of the channel

        :rtype: str
        :returns: the guid of the parent item

        """

        parent_guid = parent.guid if parent else channel_guid
        if parent_guid is None:
            raise ValueError("No parent and not channel guid specified")

        children = children or []

        # The path is constructed like this for abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx:
        # <storepath>/ab/cd/abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        pickles_file = "{}.json".format(parent_guid.lower())
        pickles_dir = os.path.join(store_path, "pickles", parent_guid[0:2], parent_guid[2:4])
        pickles_path = os.path.join(pickles_dir, pickles_file)

        if not os.path.isdir(pickles_dir):
            os.makedirs(pickles_dir)

        content = {
            "parent": self.pickle_media_item(parent) if parent is not None else None,
            "children": {item.guid.lower(): self.pickle_media_item(item) for item in children}
        }
        with io.open(pickles_path, "w+", encoding='utf-8') as fp:
            fp.write(JsonHelper.dump(content, pretty_print=True))

        return parent_guid
