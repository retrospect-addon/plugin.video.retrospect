#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import re
import string
import urllib
import htmlentitydefs

#===============================================================================
# Make global object available
#===============================================================================
from logger import Logger


class HtmlEntityHelper:
    """Used for HTML converting"""

    def __init__(self):
        """Initialises the class"""

        raise NotImplementedError("Just statics")

    @staticmethod
    def strip_amp(data):
        """Replaces the "&amp;" with "&"

        Arguments:
        data : string - data to search and replace in.

        Returns:
        the data with replaced values.

        """

        return string.replace(data, "&amp;", "&")

    @staticmethod
    def convert_html_entities(html):
        """Convert the HTML entities into their real characters

        Arguments:
        html : string - The HTML to convert

        Returns:
        The HTML with converted characters

        """

        try:
            return HtmlEntityHelper.__convert_html_entities(html)
        except:
            Logger.error("Error converting: %s", html, exc_info=True)
            return html

    @staticmethod
    def url_encode(url):
        # type: (str) -> str
        """Converts an URL in url encode characters

        @type url: str
        @param url: the data to URL encode.

        @rtype: str
        @return: Encoded URL like this. Example: '/~connolly/' yields '/%7econnolly/'.

        """

        if isinstance(url, unicode):
            Logger.trace("Unicode url: %s", url)
            return urllib.quote(url.encode())
        else:
            # this is the main time waster
            return urllib.quote(url)

    @staticmethod
    def url_decode(url):
        # type: (str) -> str
        """Converts an URL encoded text in plain text

        @type url: str
        @param url: the URL encoded text to decode to decode

        @rtype: str
        @return: Decoded URL like this. Example: '/%7econnolly/' yields '/~connolly/'.

        """

        return urllib.unquote(url)

    @staticmethod
    def __convert_html_entities(html):
        """Convert the entities in HTML using the HTMLEntityConverter into
        their real characters.

        @type html: str
        @param html: The HTML to convert

        @rtype: str
        @return: The HTML with converted characters

        """

        return re.sub("&(#?x?)(\w+?);", HtmlEntityHelper.__html_entity_converter, html)

    @staticmethod
    def __html_entity_converter(entity):
        """Substitutes an HTML entity with the correct character

        @type entity: re.MatchObject
        @param entity: Value of the HTML entity without the '&'

        @rtype: str
        @return: Replaces &#xx where 'x' is single digit, or &...; where '.' is a
        character into the real character. That character is returned.


        """

        # Logger.Debug("1:%s, 2:%s", entity.group(1), entity.group(2))
        try:
            if entity.group(1) == "#":
                # Logger.Trace("%s: %s", entity.group(2), chr(int(entity.group(2))))
                return unichr(int(entity.group(2), 10))

            elif entity.group(1) == "#x":
                # check for hex values
                return unichr(int(entity.group(2), 16))

            elif entity.group(2) == 'apos':
                # this one is not covert in name2codepoint
                return "'"

            else:
                # Logger.Trace("%s: %s", entity.group(2), htmlentitydefs.name2codepoint[entity.group(2)])
                return unichr(htmlentitydefs.name2codepoint[entity.group(2)])
        except:
            Logger.error("Error converting HTMLEntities: &%s%s", entity.group(1), entity.group(2), exc_info=True)
            return '&%s%s;' % (entity.group(1), entity.group(2))
