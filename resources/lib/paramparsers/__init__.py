# SPDX-License-Identifier: CC-BY-NC-SA-4.0

__all__ = ["parameter", "action", "paramparser", "uriparser", "get_parser"]

from resources.lib.paramparsers.queryparser import QueryParser
from resources.lib.paramparsers.uriparser import UriParser
from resources.lib.paramparsers.paramparser import ParamParser


def get_parser(uri, add_on_name=None):
    """ Returns a specific ParamParser object to parse objects

    :param str uri:          The uri or part of the uri to parse
    :param str add_on_name:  The add-on name

    :return: a ParamParser for the URL
    :rtype: ParamParser
    """

    if "?" in uri or not uri:
        return QueryParser(uri, add_on_name)
    elif not uri.startswith("?"):
        return UriParser(uri, add_on_name)
    else:
        raise IndexError("Cannot find parser for {}".format(uri))
