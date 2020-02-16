# SPDX-License-Identifier: CC-BY-NC-SA-4.0

__all__ = ["parameters", "actions", "paramparser", "uriparser"]

from resources.lib.paramparsers.queryparser import QueryParser
from resources.lib.paramparsers.uriparser import UriParser

QUERY = "query"
URI = "uri"


def get_parser(parser_type, add_on_name):
    if parser_type == URI:
        return UriParser(add_on_name)
    elif parser_type == QUERY:
        return QueryParser(add_on_name)
    else:
        raise IndexError("Cannot find parser for {}".format(parser_type))
