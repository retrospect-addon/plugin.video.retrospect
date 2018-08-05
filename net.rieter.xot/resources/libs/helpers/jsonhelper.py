# coding:UTF-8
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
import json


#noinspection PyShadowingNames
class JsonHelper:
    def __init__(self, data, logger=None):
        """Creates a class that wraps json.

        Arguments:
        data : string - JSON data to parse

        Keyword Arguments:
        Logger : Logger - If specified it is used for logging

        """
        self.logger = logger
        self.data = data.strip()
        self.json = dict()

        if len(self.data) == 0:
            # no data in, no data out
            self.json = dict()
            return

        if self.data[0] not in "[{":
            # find the actual start in case of a jQuery18303627530449324564_1370950605750({"success":true});
            if self.logger is not None:
                self.logger.Debug("Removing non-Json wrapper")
            start = self.data.find("(") + 1
            end = self.data.rfind(")")
            self.data = self.data[start:end]

        # here we are call the json.loads
        self.json = json.loads(self.data)

    @staticmethod
    def ConvertSpecialChars(text, doQuotes=True):
        """ Converts special characters in json to their Unicode equivalents. Quotes can
        be ommitted by specifying the doQuotes as False. The input text should be able to
        hold the output format. That means that for UTF-8 charachters
        to be allowed, the string should be UTF-8 decoded because, Python will otherwise
        assume it to be ASCII.

        Arguments:
        test     : string  - the text to search for.

        Keyword Arguments:
        doQuotes : Boolean - Should quotes be replaced

        Returns text with all the \uXXXX values replaced with their Unicode
        characters. XXXX is considered a Hexvalue. It returns unichr(int(hex)). The
        returnvalue is UTF-8 byte encoded.

        """

        # special chars
        # unicode chars
        cleanText = re.sub("(\\\u)(.{4})", JsonHelper.__SpecialCharsHandler, text)

        # other replacements
        replacements = [("\\n", "\n"), ("\\r", "\r"), ("\\/", "/")]
        for k, v in replacements:
            cleanText = cleanText.replace(k, v)

        if doQuotes:
            cleanText = JsonHelper.__ConvertQuotes(cleanText)

        return cleanText

    @staticmethod
    def __ConvertQuotes(text):
        """ Replaces escaped quotes with their none escaped ones.

        Arguments:
        text : String - The input text to clean.

        """

        cleanText = text
        replacements = [('\\"', '"'), ("\\'", "'")]

        for k, v in replacements:
            cleanText = cleanText.replace(k, v)

        return cleanText

    @staticmethod
    def __SpecialCharsHandler(match):
        """ Helper method to replace \uXXXX with unichr(int(hex))

        Arguments:
        match : RegexMatch - the matched element in which group(2) holds the
                             hex value.

        Returns the Unicode character corresponding to the Hex value.

        """

        hexString = "0x%s" % (match.group(2))
        # print hexString
        hexValue = int(hexString, 16)
        return unichr(hexValue)

    #noinspection PyUnboundLocalVariable
    def GetValue(self, *args, **kwargs):
        """ Retrieves data from the JSON object based on the input parameters

        @param args:    the dictionary keys, or list indexes
        @param kwargs:  possible value = fallback and allows the specification of a fallback value

        @return: the selected JSON object

        """

        try:
            data = self.json
            for arg in args:
                data = data[arg]
        except KeyError:
            if "fallback" in kwargs:
                if self.logger:
                    self.logger.Debug("Key ['%s'] not found in Json", arg)
                return kwargs["fallback"]

            if self.logger:
                self.logger.Warning("Key ['%s'] not found in Json", arg, exc_info=True)
            return None

        return data

    @staticmethod
    def DictionaryToString(dictionary):
        """ Converts a dictionary into a set of lines 'key': 'value'

        @param dictionary: the input dictionary
        @return: string representation
        """

        return reduce(lambda x, y: "%s'%s': '%s'\n" % (x, y, dictionary[y]), dictionary, "Dictionary:\n")

    @staticmethod
    def Dump(dictionary, prettyPrint=True):
        """ Dumps a JSON object to a string

        @param prettyPrint:     (boolean) indicating if the format should be nice
        @param dictionary: (string) the object to dump

        @return: a valid JSON string
        """

        if prettyPrint:
            return json.dumps(dictionary, indent=4)
        else:
            return json.dumps(dictionary)

    @staticmethod
    def Loads(jsonData):
        """ Loads a JSON object to a valid object

        @param jsonData:   (string) the JSON data to load

        @return: a valid JSON object
        """

        return json.loads(jsonData)

    def __str__(self):
        return self.data
