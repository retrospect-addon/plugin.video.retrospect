# SPDX-License-Identifier: CC-BY-NC-SA-4.0

__all__ = ["parameter", "action", "paramparser", "uriparser", "get_parser"]

from resources.lib.paramparsers.queryparser import QueryParser
from resources.lib.paramparsers.uriparser import UriParser
from resources.lib.paramparsers.paramparser import ParamParser


def get_parser(add_on_id, full_url=None, add_on_path=None, query=None):
    """ Returns a specific ParamParser object to parse objects

    :param str add_on_id:      The id of the add-on
    :param str full_url:       The full url to parse
    :param str add_on_path:    The add-on path (plugin://<addon-id>/path/)
    :param str query:          The uri or part of the uri to parse

    :return: a ParamParser for the URL
    :rtype: ParamParser

    Either specify the full_url or the query and add_on_path

    """

    # Make sure the inputs are correct
    if full_url and "?" in full_url:
        add_on_path, query = full_url.split("?")
    elif full_url:
        add_on_path = full_url

    if query:
        return QueryParser(add_on_id, add_on_path, query)
    elif add_on_path.count("/") == 3:
        # the parser to use for add-on entry
        return QueryParser(add_on_id, add_on_path, query)
    elif add_on_path:
        return UriParser(add_on_id, add_on_path, query)
    else:
        raise IndexError("Cannot find parser for {}{}{}".
                         format(add_on_path, "?" if query else "", query))
