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

        return

    @staticmethod
    def StripAmp(data):
        """Replaces the "&amp;" with "&"

        Arguments:
        data : string - data to search and replace in.

        Returns:
        the data with replaced values.

        """

        return string.replace(data, "&amp;", "&")

    @staticmethod
    def ConvertURLEntities(url):
        """Convert the URL entities into their real characters

        Arguments:
        url : string - The URL to convert

        Returns:
        The URL with converted characters

        """

        htmlHelper = HtmlEntityHelper()
        return htmlHelper.__ConvertURLEntities(url)

    @staticmethod
    def ConvertHTMLEntities(html):
        """Convert the HTML entities into their real characters

        Arguments:
        html : string - The HTML to convert

        Returns:
        The HTML with converted characters

        """

        try:
            htmlHelper = HtmlEntityHelper()
            return htmlHelper.__ConvertHTMLEntities(html)
        except:
            Logger.Error("Error converting: %s", html, exc_info=True)
            return html

    @staticmethod
    def UrlEncode(url):
        """Converts an URL in url encode characters

        Arguments:
        url : string - the URL to encode.

        Returns:
        encoded URL like this.

        Example: '/~connolly/' yields '/%7econnolly/'.

        """

        htmlHelper = HtmlEntityHelper()
        return htmlHelper.__UrlEncode(url)

    @staticmethod
    def UrlDecode(url):
        """Converts an URL encoded text in plain text

        Arguments:
        url : string - the URL to decode.

        Returns:
        decoded URL like this.

        Example: '/%7econnolly/' yields '/~connolly/'.

        """

        return urllib.unquote(url)

    def __UrlEncode(self, url):
        """Converts an URL in url encode characters

        Arguments:
        url : string - the URL to encode.

        Returns:
        encoded URL like this.

        Example: '/~connolly/' yields '/%7econnolly/'.

        """

        # some Unicode characters cannot be quoted so
        # we should encode first
        if isinstance(url, unicode):
            Logger.Trace("Unicode url: %s", url)
            return urllib.quote(url.encode())
        else:
            # this is the main time waster
            return urllib.quote(url)

    def __ConvertHTMLEntities(self, html):
        """Convert the entities in HTML using the HTMLEntityConverter into
        their real characters.

        Arguments:
        html : string - The HTML to convert

        Returns:
        The HTML with converted characters

        """

        return re.sub("&(#?x?)(\w+?);", self.__HTMLEntityConverter, html)

    def __ConvertURLEntities(self, url):
        """Convert the entities in an URL using the UrlEntityConverter into
        their real characters.

        Arguments:
        url : string - The URL to convert

        Returns:
        The URL with converted characters

        """

        newUrl = re.sub("(%)([1234567890ABCDEF]{2})", self.__UrlEntityConverter, url)
        return newUrl

    def __HTMLEntityConverter(self, entity):
        """Substitutes an HTML entity with the correct character

        Arguments:
        entity - string - Value of the HTML entity without the '&'

        Returns:
        Replaces &#xx where 'x' is single digit, or &...; where '.' is a
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
                # Logger.Trace("%s: %s", entity.group(2), htmlentitydefs.entitydefs[entity.group(2)])
                # return htmlentitydefs.entitydefs[entity.group(2).lower()]
                return unichr(htmlentitydefs.name2codepoint[entity.group(2)])
                # return chr(htmlentitydefs.name2codepoint[entity.group(2)])
        except:
            Logger.Error("Error converting HTMLEntities: &%s%s", entity.group(1), entity.group(2), exc_info=True)
            return '&%s%s;' % (entity.group(1), entity.group(2))
        # return entity

    def __UrlEntityConverter(self, entity):
        """Substitutes an URL entity with the correct character

        Arguments:
        entity - string - Value of the URL entity without the '%'

        Returns:
        Replaces %xx where x is single digit into the real character. That
        character is returned.

        """

        # Logger.Debug("1:%s, 2:%s", entity.group(1), entity.group(2))
        try:
            tmpHex = '0x%s' % (entity.group(2))
            # Logger.Debug(int(tmpHex, 16))
            return chr(int(tmpHex, 16))
        except:
            Logger.Error("error converting URLEntities", exc_info=True)
            return '%s%s' % (entity.group(1), entity.group(2))


if __name__ == "__main__":

    def Test():
        Logger.CreateLogger("c:\\temp\\test.log", "HTML EntityHelper Test", 0, False)
        chars = {"&amp;": "&",
                 "&apos;": "'",
                 "&#100;": "d",
                 "&gt;": ">",
                 "&#39;": "'",
                 "&#039;": "'",
                 "&#x27;": "'",
                 "&quot;": '"'}
        for char in chars:
            val = HtmlEntityHelper.ConvertHTMLEntities(char)
            print "%-7s: %s -> %s - %s" % (val == chars[char], char, val, chars[char])

    def Display():
        keys = htmlentitydefs.name2codepoint.keys()
        keys.sort()
        for k in keys:
            print "%s : %s" % (k, htmlentitydefs.name2codepoint[k])

    Test()
    # Display()

    # import cProfile
    # cProfile.run("Test()")
