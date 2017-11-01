#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import time
import os

from regexer import Regexer
from config import Config
from logger import Logger
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.encodinghelper import EncodingHelper


class SubtitleHelper:
    """Helper class that is used for handling subtitle files."""

    # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    ANSIColours = {
        "<30>": '<font color="#000000">',  # Black
        "<31>": '<font color="#ff0000">',  # Red
        "<32>": '<font color="#00ff00">',  # Green
        "<33>": '<font color="#ffff00">',  # Brown/Yellow
        "<34>": '<font color="#0000ff">',  # Blue
        "<35>": '<font color="#ff00ff">',  # Magenta
        "<36>": '<font color="#00ffff">',  # Cyan
        "<37>": '<font color="#ffffff">',  # Gray
        "</30>": "</font>",
        "</31>": "</font>",
        "</32>": "</font>",
        "</33>": "</font>",
        "</34>": "</font>",
        "</35>": "</font>",
        "</36>": "</font>",
        "</37>": "</font>",
    }

    def __init__(self):
        """Create a class instance. This is not allowed, due to only static
        methods.

        """

        raise Exception("Not allowed to create instance of SubtitleHelper")
        pass

    # noinspection PyShadowingBuiltins
    @staticmethod
    def DownloadSubtitle(url, fileName="", format='sami', proxy=None, replace=None):
        """Downloads a SAMI and stores the SRT in the cache folder

        Arguments:
        url      : string - URL location of the SAMI file

        Keyword Arguments:
        fileName : string - Filename to use to store the subtitle in SRT format.
                            if not specified, an MD5 hash of the URL with .xml
                            extension will be used
        format : string   - defines the source format. Defaults to Sami.

        Returns:
        The full patch of the cached SRT file.

        """

        if fileName == "":
            Logger.Debug("No filename present, generating filename using MD5 hash of url.")
            fileName = "%s.srt" % (EncodingHelper.EncodeMD5(url),)
        elif not fileName.endswith(".srt"):
            Logger.Debug("No SRT extension present, appending it.")
            fileName = "%s.srt" % (fileName, )

        srt = ""
        try:
            localCompletePath = os.path.join(Config.cacheDir, fileName)

            # no need to download it again!
            if os.path.exists(localCompletePath):
                return localCompletePath

            Logger.Trace("Opening Subtitle URL")
            raw = UriHandler.Open(url, proxy=proxy)

            if raw == "":
                Logger.Warning("Empty Subtitle path found. Not setting subtitles.")
                return ""

            # try to decode it
            try:
                raw = raw.decode()
            except:
                # fix some weird chars
                try:
                    raw = raw.replace("\x96", "-")
                except:
                    Logger.Error("Error replacing some weird chars.")
                Logger.Warning("Converting input to UTF-8 using 'unicode_escape'")
                raw = raw.decode('unicode_escape')

            if format.lower() == 'sami':
                srt = SubtitleHelper.__ConvertSamiToSrt(raw)
            elif format.lower() == 'srt':
                srt = raw
            elif format.lower() == 'webvtt':
                srt = SubtitleHelper.__ConvertWebVttToSrt(raw)
            elif format.lower() == 'ttml':
                srt = SubtitleHelper.__ConvertTtmlToSrt(raw)
            elif format.lower() == 'dcsubtitle':
                srt = SubtitleHelper.__ConvertDCSubtitleToSrt(raw)
            elif format.lower() == 'json':
                srt = SubtitleHelper.__ConvertJsonSubtitleToSrt(raw)
            elif format.lower() == 'm3u8srt':
                srt = SubtitleHelper.__ConvertM3u8SrtToSubtitleToSrt(raw, url, proxy)
            else:
                error = "Uknown subtitle format: %s" % (format,)
                raise NotImplementedError(error)

            if replace:
                Logger.Debug("Replacing SRT data: %s", replace)
                for needle in replace:
                    srt = srt.replace(needle, replace[needle])

            f = open(localCompletePath, 'w')
            f.write(srt)
            f.close()
            Logger.Info("Saved SRT as %s", localCompletePath)
            return localCompletePath
        except:
            Logger.Error("Error handling Subtitle file: [%s]", srt, exc_info=True)
            return ""

    @staticmethod
    def __ConvertJsonSubtitleToSrt(jsonSubtitle):
        """Converts Json Subtitle format into SRT format:

        Arguments:
        jsonSubtitle : string - Json Subtitle subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            {"startMillis":80,"endMillis":4170,"text":"Ett Kanal 5:\nAlla gonblick i \"100 jdare!!!\"?","posX":0.5,"posY":0.9,"colorR":220,"colorG":220,"colorB":220}

        Returns
            1
            00:00:20,000 --> 00:00:24,400
            text

        The format of the timecode is Hours:Minutes:Seconds:Ticks where a "Tick"
        is a value of between 0 and 249 and lasts 4 milliseconds.

        """

        regex = '"startMillis":(\d+),"endMillis":(\d+),"text":"(.+?)(?=["] *,)'
        subs = Regexer.DoRegex(regex, jsonSubtitle)

        # Init some stuff
        srt = ""
        i = 1

        for sub in subs:
            try:
                # print sub
                start = SubtitleHelper.__ConvertToTime(sub[0])
                end = SubtitleHelper.__ConvertToTime(sub[1])

                text = sub[2].replace('\"', '"')
                text = JsonHelper.ConvertSpecialChars(text)
                text = HtmlEntityHelper.ConvertHTMLEntities(text)
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                i += 1
            except:
                Logger.Error("Error parsing subtitle: %s", sub, exc_info=True)

        return srt

    @staticmethod
    def __ConvertDCSubtitleToSrt(dcSubtitle):
        """Converts DC Subtitle format into SRT format:

        Arguments:
        dcSubtitle : string - DC Subtitle subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            <Subtitle SpotNumber="1" TimeIn="00:00:01:220" TimeOut="00:00:04:001" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 1</Text>
            </Subtitle>
            <Subtitle SpotNumber="2" TimeIn="00:02:07:180" TimeOut="00:02:10:040" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 1</Text>
            </Subtitle>
            <Subtitle SpotNumber="3" TimeIn="00:02:15:190" TimeOut="00:02:17:190" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 1</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 2</Text>
            </Subtitle>
            <Subtitle SpotNumber="4" TimeIn="00:03:23:140" TimeOut="00:03:30:120" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 1</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 2</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 3</Text>
            </Subtitle>

        Returns
            1
            00:00:20,000 --> 00:00:24,400
            text

        The format of the timecode is Hours:Minutes:Seconds:Ticks where a "Tick"
        is a value of between 0 and 249 and lasts 4 milliseconds.

        """

        # parseRegex = '<subtitle[^>]+spotnumber="(\d+)" timein="(\d+:\d+:\d+):(\d+)" timeout="(\d+:\d+:\d+):(\d+)"[^>]+>\W+<text[^>]+>([^<]+)</text>\W+(?:<text[^>]+>([^<]+)</text>)*\W+</subtitle>'
        parseRegex = '<subtitle[^>]+spotnumber="(\d+)" timein="(\d+:\d+:\d+):(\d+)" timeout="(\d+:\d+:\d+):(\d+)"[^>]+>|<text[^>]+>([^<]+)</text>'
        parseRegex = parseRegex.replace('"', '["\']')
        subs = Regexer.DoRegex(parseRegex, dcSubtitle)

        srt = ""
        i = 1
        text = ""
        start = ""
        end = ""

        for sub in subs:
            #Logger.Trace(sub)
            try:
                if sub[0]:
                    # new start of a sub
                    if text and start and end:
                        # if we have a complete old one, save it
                        text = HtmlEntityHelper.ConvertHTMLEntities(text)
                        srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                        i += 1
                    start = "%s,%03d" % (sub[1], int(sub[2]))
                    end = "%s,%03d" % (sub[3], int(sub[4]))
                    text = ""
                else:
                    text = "%s\n%s" % (text, sub[5].replace("<br />", "\n"))
            except:
                Logger.Error("Error parsing subtitle: %s", sub, exc_info=True)
        return srt

    @staticmethod
    def __ConvertWebVttToSrt(webvvt):
        """Converts sami format into SRT format:

        Arguments:
        ttml : string - TTML (Timed Text Markup Language) subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """

        count = 0
        result = ""
        for line in webvvt.split("\n"):
            line = line.strip()
            if line.endswith("WEBVTT"):
                continue
            if not line:
                continue

            if " --> " in line:
                count += 1
                start, end = line.split(" --> ")
                result = "%s\n\n%s" % (result, count)
                if start.count(":") == 1:
                    result = "%s\n00:%s --> 00:%s" % (result, start.replace(".", ","), end.replace(".", ","))
                else:
                    result = "%s\n%s --> %s" % (result, start.replace(".", ","), end.replace(".", ","))
            else:
                result = "%s\n%s" % (result, line)

        return result

    @staticmethod
    def __ConvertTtmlToSrt(ttml):
        """Converts sami format into SRT format:

        Arguments:
        ttml : string - TTML (Timed Text Markup Language) subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """

        parsRegex = '<p[^>]+begin="([^"]+)\.(\d+)"[^>]+end="([^"]+)\.(\d+)"[^>]*>([\w\W]+?)</p>'
        subs = Regexer.DoRegex(parsRegex, ttml)

        srt = ""
        i = 1

        for sub in subs:
            try:
                # print sub
                start = "%s,%03d" % (sub[0], int(sub[1]))
                end = "%s,%03d" % (sub[2], int(sub[3]))
                text = sub[4].replace("<br />", "\n")
                # text = sub[4].replace("<br />", "\n")
                text = HtmlEntityHelper.ConvertHTMLEntities(text)
                text = text.replace("\r\n", "")
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                i += 1
            except:
                Logger.Error("Error parsing subtitle: %s", sub[1], exc_info=True)

        return srt

    @staticmethod
    def __ConvertSamiToSrt(sami):
        """Converts sami format into SRT format:

        Arguments:
        sami : string - SAMI subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """
        parsRegex = '<sync start="(\d+)"><p[^>]+>([^<]+)</p></sync>\W+<sync start="(\d+)">'
        subs = Regexer.DoRegex(parsRegex, sami)

        if len(subs) == 0:
            parsRegex2 = '<sync start=(\d+)>\W+<p[^>]+>([^\n]+)\W+<sync start=(\d+)>'
            subs = Regexer.DoRegex(parsRegex2, sami)

        srt = ""
        i = 1

        for sub in subs:
            try:
                # print sub
                start = SubtitleHelper.__ConvertToTime(sub[0])
                end = SubtitleHelper.__ConvertToTime(sub[2])
                text = sub[1]
                text = HtmlEntityHelper.ConvertHTMLEntities(text)
                # text = sub[1]
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text)
                i += 1
            except:
                Logger.Error("Error parsing subtitle: %s", sub[1], exc_info=True)

        # re-encode to be able to write it
        return srt

    @staticmethod
    def __ConvertM3u8SrtToSubtitleToSrt(raw, url, proxy):
        # Find the VTT line in the subtitle
        lines = raw.split("\n")
        subUrl = None
        for line in lines:
            if ".vtt" in line:
                subUrl = line
                break

        if not subUrl:
            return ""

        if not subUrl.startswith("http"):
            subUrl = "%s/%s" % (url.rsplit("/", 1)[0], subUrl)

        # Now we know the subtitle, it would be wise to just use the existing converters to just
        # convert the data, but now now
        result = ""
        m3u8Sub = UriHandler.Open(subUrl, proxy=proxy)
        # Again decode the data
        try:
            m3u8Sub = m3u8Sub.decode()
        except:
            Logger.Warning("Converting input to UTF-8 using 'unicode_escape'")
            m3u8Sub = m3u8Sub.decode('unicode_escape')

        for line in m3u8Sub.split("\n"):
            line = line.strip()
            if line.endswith("WEBVTT") or line.startswith("X-TIMESTAMP"):
                continue

            if " --> " in line:
                start, end = line.split(" --> ")
                if start.count(":") == 1:
                    result = "%s\n00:%s --> 00:%s" % (result, start.replace(".", ","), end.replace(".", ","))
                else:
                    result = "%s\n%s --> %s" % (result, start.replace(".", ","), end.replace(".", ","))
            else:
                result = "%s\n%s" % (result, line)

        return result

    @staticmethod
    def __ConvertToTime(timestamp):
        """Converts a SAMI (msecs since start) timestamp into a SRT timestamp

        Arguments:
        timestamp : string - SAMI timestamp

        Returns:
        SRT timestamp (00:04:53,920)

        """
        msecs = timestamp[-3:]
        secs = int(timestamp) / 1000
        sync = time.strftime("%H:%M:%S", time.gmtime(secs)) + ',' + msecs
        return sync
