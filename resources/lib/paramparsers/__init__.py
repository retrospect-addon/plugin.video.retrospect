# SPDX-License-Identifier: CC-BY-NC-SA-4.0

__all__ = ["parameter", "action", "paramparser", "uriparser", "get_parser"]

from resources.lib.paramparsers.queryparser import QueryParser
from resources.lib.paramparsers.uriparser import UriParser
from resources.lib.paramparsers.paramparser import ParamParser


def get_parser(parameters, add_on_name):
    """ Returns a specific ParamParser object to parse objects

    :param str parameters:   The parameters to parse
    :param str add_on_name:  The add-on name

    :return: a ParamParser for the URL
    :rtype: ParamParser
    """

    if parameters.startswith("/"):
        return UriParser(add_on_name, parameters)
    elif parameters.startswith("?") or not parameters:
        return QueryParser(add_on_name, parameters)
    else:
        raise IndexError("Cannot find parser for {}".format(parameters))
