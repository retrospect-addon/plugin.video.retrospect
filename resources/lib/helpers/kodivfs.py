# SPDX-License-Identifier: GPL-3.0-or-later

import xbmcvfs


class File(object):
    def __init__(self, path, flags="r"):
        """ Wrapper for xbmcvfs.File class with __enter__() and __exit__()

        :param str path:    The file or directory to open
        :param str flags:   The flags used to open the file

        """

        self.flags = flags
        self.path = path

        self.__file = None

    def __enter__(self):
        """ Enter the File block

        :rtype: xbmcvfs.File

        """

        self.__file = xbmcvfs.File(self.path, self.flags)
        return self.__file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Exiting """
        self.__file.close()
        del self.__file
