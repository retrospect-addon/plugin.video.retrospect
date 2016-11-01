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

# doing some dynamic loading depending on the availability of json modules
_jsonLoaded = False
_jsonLib = "localjson"
try:
    if not _jsonLoaded:
        import json
        _jsonLoaded = True
        _jsonLib = "json-%s" % (json.__version__,)
except:
    pass

try:
    if not _jsonLoaded:
        # noinspection PyUnresolvedReferences
        import simplejson as json
        _jsonLoaded = True
        _jsonLib = "simplejson-%s" % (json.__version__,)
except:
    pass


#noinspection PyShadowingNames
class JsonHelper:
    def __init__(self, data, logger=None):
        """Creates a class that wraps json, simplejson or MyJson.

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
        try:
            if self.logger is not None:
                self.logger.Trace("Parsing JSON using: %s", _jsonLib)

            if _jsonLoaded:
                self.json = json.loads(self.data)
            else:
                self.json = JsonHelper.MyJson(logger).loads(self.data)
        except:
            if self.logger is not None:
                self.logger.Warning("Falling back to MyJson", exc_info=True)
            self.json = JsonHelper.MyJson().loads(self.data)

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
        return JsonHelper.MyJson.ConvertSpecialChars(text, doQuotes)

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
        # type: (str) -> Any
        """ Loads a JSON object to a valid object

        @param jsonData:   (string) the JSON data to load

        @return: a valid JSON object
        """

        return json.loads(jsonData)

    def __str__(self):
        return self.data

    class MyJson:
        def __init__(self, logger=None):

            self.Logger = logger

            # initialize some variables
            self.quotes = "'\""
            self.keyValueEnd = ",}]"
            self.keyEnd = ":"
            self.numeric = "-01234567890."
            self.data = None
            self.__pointer = 0
            self.__maxPointer = 0

        def loads(self, data):
            self.__maxPointer = len(data)

            # do a general cleanup here at the start, much faster then for each try.
            # After this, it will be a correct encoded string. Quotes are only done
            # for strings, as we need the escaped quotes for the strings. The only
            # action in the GetValue, GetNamedValues and GetNamedValue would be the
            # quotes.
            data = data.strip()
            self.data = JsonHelper.ConvertSpecialChars(data, doQuotes=False)

            if self.Logger:
                self.Logger.Trace("Getting Json data from string")

            if self.data:
                return self.__GetJsonData()
            return dict()

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
            cleanText = re.sub("(\\\u)(.{4})", JsonHelper.MyJson.__SpecialCharsHandler, text)

            # other replacements
            replacements = [("\\n", "\n"), ("\\r", "\r"), ("\\/", "/")]
            for k, v in replacements:
                cleanText = cleanText.replace(k, v)

            if doQuotes:
                cleanText = JsonHelper.MyJson.__ConvertQuotes(cleanText)

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

        def __GetJsonData(self):
            """ actually parses the information """
            json = dict()
            try:
                if self.data[self.__pointer] == "[":
                    json = self.__ProcessList()
                elif self.data[self.__pointer] == "{":
                    json = self.__ProcessDictionary()
                elif self.__Seek("("):
                    # we found a bracket, start there (we need to do a read one more char
                    # to actually start inside the (
                    self.__Read(offset=2)
                    self.__GetJsonData()
                else:
                    json = dict()
                    if self.Logger:
                        self.Logger.Warning("No valid JSON data found")

            except Exception, e:
                error = "%s at %s: %s>>>%s<<<%s" % (e, self.__pointer, self.data[self.__pointer - 25:self.__pointer], self.data[self.__pointer], self.data[self.__pointer + 1:self.__pointer + 25])
                #noinspection PyPropertyAccess
                e.args = (error,)
                raise

            return json

        def __ProcessDictionary(self):
            """ Processes a Json ictionary. That is an containter that has { as
                an opener

            """

            dictionary = dict()
            data = ""
            key = None

            char = self.__Read(True)
            # while not char is None:
            while char:
                if char in self.keyValueEnd:
                    if key is not None:
                        dictionary[key] = data

                    data = ""
                    key = None

                    if char == "}":
                        break

                elif char == "{":
                    if key is None:
                        raise AttributeError("Data is needed for a key")

                    data = self.__ProcessDictionary()

                elif char == "[":
                    if key is None:
                        raise AttributeError("Data is needed for a key")

                    data = self.__ProcessList()

                elif char in self.quotes:
                    data = self.__ProcessString()

                elif char in self.numeric:
                    data = self.__ProcessNumber()

                elif char in "tTfFnN" and key is not None:
                    data = self.__ProcessBool()

                elif char in self.keyEnd:
                    if data is None:
                        raise AttributeError("Data is needed for a key")

                    key = data
                    data = ""
                else:
                    if key is not None:
                        # if we are reading a key, the quotes are optional
                        raise NotImplementedError(char)
                    else:
                        # rewind to get the current char in the next read
                        self.__Move(-1)
                        data = self.__ProcessString(":")
                        # rewind
                        self.__Move(-1)
                    # data = data + char

                char = self.__Read(True)

            return dictionary

        def __ProcessList(self):
            """ Processes a Json list. That is a container with a [
                as an opener.

            """

            listItems = []

            char = self.__Read(True)
            # while not char is None:
            while char:
                if char == "{":
                    listItems.append(self.__ProcessDictionary())

                elif char == "[":
                    listItems.append(self.__ProcessList())

                elif char == "]":
                    break

                elif char in self.quotes:
                    listItems.append(self.__ProcessString())

                elif char in self.numeric:
                    listItems.append(self.__ProcessNumber())

                elif char in "tTfF":
                    listItems.append(self.__ProcessBool())

                elif char == ",":
                    pass

                else:
                    raise NotImplementedError(char)
                    # data = data + char

                char = self.__Read(True)

            return listItems

        def __ProcessBool(self):
            """ Reads a boolean from the data. The pointer should be at
            the first part character of the boolean. self.__Read(0) should
            return either F or T.

            """

            char = self.__Read(offset=0)
            if char.lower() == "t":
                data = True
                self.__Move(3)
            elif char.lower() == "n":
                data = None
                self.__Move(3)
            else:
                data = False
                self.__Move(4)

            return data

        def __ProcessNumber(self):
            """ Reads a number of the data. The pointer should be at
            the first part character of the number. self.__Read(0) should
            return a valid numberic value.

            """

            # where do we start
            startIndex = self.__pointer

            if self.__Seek(self.keyValueEnd):
                # the next read will be one from the self.keyValueEnd
                data = self.data[startIndex:self.__pointer + 1]
            else:
                raise EOFError

            if "." in data:
                data = float(data)
            else:
                data = int(data)

            return data

        def __ProcessString(self, quoteChar=None):
            """Reads a string from the data. The pointer should be at
            the first quote character. self.__Read(0) should return a " or '.

            """

            data = ""

            if quoteChar is None:
                # quoteChar was not passed. Look at the current char
                quoteChar = self.__Peek(0)

            # move to the next char, no need for reading
            startIndex = self.__pointer + 1

            # and then find the next quoteChar
            escapedQuotesPresent = False
            while self.__Seek(quoteChar):
                # if we find the quote-char and it was not escaped, the
                # we are at the end of it all.
                self.__Read()
                if self.__Peek(-1) != "\\":
                    data = self.data[startIndex:self.__pointer]
                    break
                else:
                    # as we already positioned the pointer one forward, we can just
                    # continue from that location
                    escapedQuotesPresent = True
                    pass

            # if escaped quotes were found, replace them
            if escapedQuotesPresent:
                return JsonHelper.MyJson.__ConvertQuotes(data)
            else:
                return data

        def __Move(self, offset):
            """ Moves the pointer relatively to it's current position

            Arguments:
            offset : Integer - the offset to move.

            The new absolute position is returned.

            """

            self.__pointer += offset
            return self.__pointer

        def __Read(self, strip=False, offset=1):
            """ Reads a char from the data

            Keyword Arguments:
            strip  : Boolean - Should whitespaces be ignored?
            offset : Integer - Where should we read. Default is next char (offset = 1).


            Returns the char the the new pointer location

            """

            self.__pointer += offset
            if self.__pointer >= self.__maxPointer:
                return None

            if strip:
                while self.data[self.__pointer].isspace() and self.__pointer <= self.__maxPointer:
                    self.__pointer += 1
                    # if self.__pointer >= self.__maxPointer:
                    #    return None

                if self.__pointer >= self.__maxPointer:
                    return None

            return self.data[self.__pointer]

        def __Peek(self, offset=1):
            """ returns the char at the next pointer position or relative to it

            Keyword arguments:
            offset : Integer - Where to read. Defaults is 1 ahead (offset = 1)


            Returns the char the that position but does not move the pointer.

            """

            return self.data[self.__pointer + offset]

        def __Seek(self, needles):
            """ Seeks for the first needle in needles. It starts searching at the
            next pointer location (+1).

            Argument:
            needles : List[String] - the needles the search for.

            Returns True if a needle was found, False otherwise. The pointer is
            positioned so the next read will retrieve the needle that was found.

            """

            self.__Move(1)

            nextIndex = self.__maxPointer + 256  # just a random location past the end
            for needle in needles:
                thisNextIndex = self.data.find(needle, self.__pointer)
                if 0 <= thisNextIndex < nextIndex:
                    nextIndex = thisNextIndex

            if nextIndex == self.__maxPointer + 256:
                # apparently no smaller item was found, so on results
                return False

            # set the pointer so the next read retrieves the char that was being
            # searched for.
            self.__pointer = nextIndex - 1
            return True
