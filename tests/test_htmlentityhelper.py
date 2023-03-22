# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

from future.utils import PY2

import unittest
import sys

if PY2:
    # noinspection PyCompatibility,PyUnresolvedReferences
    reload(sys)  # We need UTF-8
    # noinspection PyUnresolvedReferences
    sys.setdefaultencoding("utf-8")  # @UndefinedVariable


from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.logger import Logger


class TestHtmlEntityHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestHtmlEntityHelper, cls).setUpClass()
        Logger.create_logger(None, str(cls), min_log_level=0)

    def test_no_constructor(self):
        with self.assertRaises(NotImplementedError):
            HtmlEntityHelper()

    def test_basic_numeric_htmlentities(self):
        chars = {
            "&#32;": u" ",  # space
            "&#33;": u"!",  # exclamation point
            "&#34;": u"\"",  # double quotes
            "&#35;": u"#",  # number sign
            "&#36;": u"$",  # dollar sign
            "&#37;": u"%",  # percent sign
            "&#38;": u"&",  # ampersand
            "&#39;": u"'",  # single quote
            "&#40;": u"(",  # opening parenthesis
            "&#41;": u")",  # closing parenthesis
            "&#42;": u"*",  # asterisk
            "&#43;": u"+",  # plus sign
            "&#44;": u",",  # comma
            "&#45;": u"-",  # minus sign - hyphen
            "&#46;": u".",  # period
            "&#47;": u"/",  # slash
            "&#48;": u"0",  # zero
            "&#49;": u"1",  # one
            "&#50;": u"2",  # two
            "&#51;": u"3",  # three
            "&#52;": u"4",  # four
            "&#53;": u"5",  # five
            "&#54;": u"6",  # six
            "&#55;": u"7",  # seven
            "&#56;": u"8",  # eight
            "&#57;": u"9",  # nine
            "&#58;": u":",  # colon
            "&#59;": u";",  # semicolon
            "&#60;": u"<",  # less than sign
            "&#61;": u"=",  # equal sign
            "&#62;": u">",  # greater than sign
            "&#63;": u"?",  # question mark
            "&#64;": u"@",  # at symbol
            "&#65;": u"A",  #
            "&#66;": u"B",  #
            "&#67;": u"C",  #
            "&#68;": u"D",  #
            "&#69;": u"E",  #
            "&#70;": u"F",  #
            "&#71;": u"G",  #
            "&#72;": u"H",  #
            "&#73;": u"I",  #
            "&#74;": u"J",  #
            "&#75;": u"K",  #
            "&#76;": u"L",  #
            "&#77;": u"M",  #
            "&#78;": u"N",  #
            "&#79;": u"O",  #
            "&#80;": u"P",  #
            "&#81;": u"Q",  #
            "&#82;": u"R",  #
            "&#83;": u"S",  #
            "&#84;": u"T",  #
            "&#85;": u"U",  #
            "&#86;": u"V",  #
            "&#87;": u"W",  #
            "&#88;": u"X",  #
            "&#89;": u"Y",  #
            "&#90;": u"Z",  #
            "&#91;": u"[",  # opening bracket
            "&#92;": u"\\",  # backslash
            "&#93;": u"]",  # closing bracket
            "&#94;": u"^",  # caret - circumflex
            "&#95;": u"_",  # underscore
            "&#96;": u"`",  # grave accent
            "&#97;": u"a",  #
            "&#98;": u"b",  #
            "&#99;": u"c",  #
            "&#100;": u"d",  #
            "&#101;": u"e",  #
            "&#102;": u"f",  #
            "&#103;": u"g",  #
            "&#104;": u"h",  #
            "&#105;": u"i",  #
            "&#106;": u"j",  #
            "&#107;": u"k",  #
            "&#108;": u"l",  #
            "&#109;": u"m",  #
            "&#110;": u"n",  #
            "&#111;": u"o",  #
            "&#112;": u"p",  #
            "&#113;": u"q",  #
            "&#114;": u"r",  #
            "&#115;": u"s",  #
            "&#116;": u"t",  #
            "&#117;": u"u",  #
            "&#118;": u"v",  #
            "&#119;": u"w",  #
            "&#120;": u"x",  #
            "&#121;": u"y",  #
            "&#122;": u"z",  #
            "&#123;": u"{",  # opening brace
            "&#124;": u"|",  # vertical bar
            "&#125;": u"}",  # closing brace
            "&#126;": u"~",  # equivalency sign - tilde
            "&#160;": chr(160),  # non-breaking space
            "&#161;": u"¡",  # inverted exclamation mark
            "&#162;": u"¢",  # cent sign
            "&#163;": u"£",  # pound sign
            "&#164;": u"¤",  # currency sign
            "&#165;": u"¥",  # yen sign
            "&#166;": u"¦",  # broken vertical bar
            "&#167;": u"§",  # section sign
            "&#168;": u"¨",  # spacing diaeresis - umlaut
            "&#169;": u"©",  # copyright sign
            "&#170;": u"ª",  # feminine ordinal indicator
            "&#171;": u"«",  # left double angle quotes
            "&#172;": u"¬",  # not sign
            "&#173;": u"­",  # soft hyphen
            "&#174;": u"®",  # registered trade mark sign
            "&#175;": u"¯",  # spacing macron - overline
            "&#176;": u"°",  # degree sign
            "&#177;": u"±",  # plus-or-minus sign
            "&#178;": u"²",  # superscript two - squared
            "&#179;": u"³",  # superscript three - cubed
            "&#180;": u"´",  # acute accent - spacing acute
            "&#181;": u"µ",  # micro sign
            "&#182;": u"¶",  # pilcrow sign - paragraph sign
            "&#183;": u"·",  # middle dot - Georgian comma
            "&#184;": u"¸",  # spacing cedilla
            "&#185;": u"¹",  # superscript one
            "&#186;": u"º",  # masculine ordinal indicator
            "&#187;": u"»",  # right double angle quotes
            "&#188;": u"¼",  # fraction one quarter
            "&#189;": u"½",  # fraction one half
            "&#190;": u"¾",  # fraction three quarters
            "&#191;": u"¿",  # inverted question mark
            "&#192;": u"À",  # latin capital letter A with grave
            "&#193;": u"Á",  # latin capital letter A with acute
            "&#194;": u"Â",  # latin capital letter A with circumflex
            "&#195;": u"Ã",  # latin capital letter A with tilde
            "&#196;": u"Ä",  # latin capital letter A with diaeresis
            "&#197;": u"Å",  # latin capital letter A with ring above
            "&#198;": u"Æ",  # latin capital letter AE
            "&#199;": u"Ç",  # latin capital letter C with cedilla
            "&#200;": u"È",  # latin capital letter E with grave
            "&#201;": u"É",  # latin capital letter E with acute
            "&#202;": u"Ê",  # latin capital letter E with circumflex
            "&#203;": u"Ë",  # latin capital letter E with diaeresis
            "&#204;": u"Ì",  # latin capital letter I with grave
            "&#205;": u"Í",  # latin capital letter I with acute
            "&#206;": u"Î",  # latin capital letter I with circumflex
            "&#207;": u"Ï",  # latin capital letter I with diaeresis
            "&#208;": u"Ð",  # latin capital letter ETH
            "&#209;": u"Ñ",  # latin capital letter N with tilde
            "&#210;": u"Ò",  # latin capital letter O with grave
            "&#211;": u"Ó",  # latin capital letter O with acute
            "&#212;": u"Ô",  # latin capital letter O with circumflex
            "&#213;": u"Õ",  # latin capital letter O with tilde
            "&#214;": u"Ö",  # latin capital letter O with diaeresis
            "&#215;": u"×",  # multiplication sign
            "&#216;": u"Ø",  # latin capital letter O with slash
            "&#217;": u"Ù",  # latin capital letter U with grave
            "&#218;": u"Ú",  # latin capital letter U with acute
            "&#219;": u"Û",  # latin capital letter U with circumflex
            "&#220;": u"Ü",  # latin capital letter U with diaeresis
            "&#221;": u"Ý",  # latin capital letter Y with acute
            "&#222;": u"Þ",  # latin capital letter THORN
            "&#223;": u"ß",  # latin small letter sharp s - ess-zed
            "&#224;": u"à",  # latin small letter a with grave
            "&#225;": u"á",  # latin small letter a with acute
            "&#226;": u"â",  # latin small letter a with circumflex
            "&#227;": u"ã",  # latin small letter a with tilde
            "&#228;": u"ä",  # latin small letter a with diaeresis
            "&#229;": u"å",  # latin small letter a with ring above
            "&#230;": u"æ",  # latin small letter ae
            "&#231;": u"ç",  # latin small letter c with cedilla
            "&#232;": u"è",  # latin small letter e with grave
            "&#233;": u"é",  # latin small letter e with acute
            "&#234;": u"ê",  # latin small letter e with circumflex
            "&#235;": u"ë",  # latin small letter e with diaeresis
            "&#236;": u"ì",  # latin small letter i with grave
            "&#237;": u"í",  # latin small letter i with acute
            "&#238;": u"î",  # latin small letter i with circumflex
            "&#239;": u"ï",  # latin small letter i with diaeresis
            "&#240;": u"ð",  # latin small letter eth
            "&#241;": u"ñ",  # latin small letter n with tilde
            "&#242;": u"ò",  # latin small letter o with grave
            "&#243;": u"ó",  # latin small letter o with acute
            "&#244;": u"ô",  # latin small letter o with circumflex
            "&#245;": u"õ",  # latin small letter o with tilde
            "&#246;": u"ö",  # latin small letter o with diaeresis
            "&#247;": u"÷",  # division sign
            "&#248;": u"ø",  # latin small letter o with slash
            "&#249;": u"ù",  # latin small letter u with grave
            "&#250;": u"ú",  # latin small letter u with acute
            "&#251;": u"û",  # latin small letter u with circumflex
            "&#252;": u"ü",  # latin small letter u with diaeresis
            "&#253;": u"ý",  # latin small letter y with acute
            "&#254;": u"þ",  # latin small letter thorn
            "&#255;": u"ÿ",  # latin small letter y with diaeresis
            "&#338;": u"Œ",  # latin capital letter OE
            "&#339;": u"œ",  # latin small letter oe
            "&#352;": u"Š",  # latin capital letter S with caron
            "&#353;": u"š",  # latin small letter s with caron
            "&#376;": u"Ÿ",  # latin capital letter Y with diaeresis
            "&#402;": u"ƒ",  # latin small f with hook - function
            "&#8211;": u"–",  # en dash
            "&#8212;": u"—",  # em dash
            "&#8216;": u"‘",  # left single quotation mark
            "&#8217;": u"’",  # right single quotation mark
            "&#8218;": u"‚",  # single low-9 quotation mark
            "&#8220;": u"“",  # left double quotation mark
            "&#8221;": u"”",  # right double quotation mark
            "&#8222;": u"„",  # double low-9 quotation mark
            "&#8224;": u"†",  # dagger
            "&#8225;": u"‡",  # double dagger
            "&#8226;": u"•",  # bullet
            "&#8230;": u"…",  # horizontal ellipsis
            "&#8240;": u"‰",  # per thousand sign
            "&#8364;": u"€",  # euro sign
            "&#8482;": u"™",  # trade mark sign
        }
        for e, v in chars.items():
            # Logger.info(u"{} -> {}".format(e, v))
            self.assertEqual(v, HtmlEntityHelper.convert_html_entities(e))

    def test_charnumber_htmlentities(self):
        chars = {
            "&#x32;": u"2",  # space
            "&#x0376;": u"Ͷ",  # space
        }
        for e, v in chars.items():
            self.assertEqual(v, HtmlEntityHelper.convert_html_entities(e))

    def test_named_htmlentities(self):
        chars = {
            "&apos;": u"'",  # Quotation mark "
            "&quot;": u"\"",  # Quotation mark "
            "&amp;": u"&",  # Ampersand &
            "&lt;": u"<",  # Less-than sign <
            "&gt;": u">",  # Greater-than sign >
            "&lsquo;": u"‘",  # Open single quote ‘
            "&rsquo;": u"’",  # Close single quote ’
            "&ldquo;": u"“",  # Open double quotes “
            "&rdquo;": u"”",  # Close double quotes ”
            "&sbquo;": u"‚",  # Single low-9 quote ‚
            "&bdquo;": u"„",  # Double low-9 quote „
            "&prime;": u"′",  # Prime/minutes/feet ′
            "&Prime;": u"″",  # Double prime/seconds/inches ″
            "&nbsp;": chr(160),  # Non-breaking space
            "&ndash;": u"–",  # En dash –
            "&mdash;": u"—",  # Em dash —
            "&ensp;": u" ",  # En space  
            "&emsp;": u" ",  # Em space  
            "&thinsp;": u" ",  # Thin space  
            "&brvbar;": u"¦",  # Broken vertical bar ¦
            "&bull;": u"•",  # Bullet •
            "&hellip;": u"…",  # Horizontal ellipsis …
            "&circ;": u"ˆ",  # Circumflex ˆ
            "&uml;": u"¨",  # Umlaut or dieresis ¨
            "&tilde;": u"˜",  # Small tilde ˜
            "&lsaquo;": u"‹",  # Single left angle quote ‹
            "&rsaquo;": u"›",  # Single right angle quote ›
            "&laquo;": u"«",  # Left angle quote; guillemotleft «
            "&raquo;": u"»",  # Right angle quote; guillemotright »
            "&oline;": u"‾",  # Overline ‾
            "&iquest;": u"¿",  # Inverted question mark ¿
            "&iexcl;": u"¡",  # Inverted exclamation ¡,
            "&cent;": u"¢",  # cent sign
            "&pound;": u"£",  # pound sign
            "&curren;": u"¤",  # currency sign
            "&yen;": u"¥",  # yen sign
            "&sect;": u"§",  # section sign
            "&copy;": u"©",  # copyright sign
            "&ordf;": u"ª",  # feminine ordinal indicator
            "&not;": u"¬",  # not sign
            "&shy;": u"­",  # soft hyphen
            "&reg;": u"®",  # registered trade mark sign
            "&macr;": u"¯",  # spacing macron - overline
            "&deg;": u"°",  # degree sign
            "&plusmn;": u"±",  # plus-or-minus sign
            "&sup2;": u"²",  # superscript two - squared
            "&sup3;": u"³",  # superscript three - cubed
            "&acute;": u"´",  # acute accent - spacing acute
            "&micro;": u"µ",  # micro sign
            "&para;": u"¶",  # pilcrow sign - paragraph sign
            "&middot;": u"·",  # middle dot - Georgian comma
            "&cedil;": u"¸",  # spacing cedilla
            "&sup1;": u"¹",  # superscript one
            "&ordm;": u"º",  # masculine ordinal indicator
            "&frac14;": u"¼",  # fraction one quarter
            "&frac12;": u"½",  # fraction one half
            "&frac34;": u"¾",  # fraction three quarters
            "&Agrave;": u"À",  # latin capital letter A with grave
            "&Aacute;": u"Á",  # latin capital letter A with acute
            "&Acirc;": u"Â",  # latin capital letter A with circumflex
            "&Atilde;": u"Ã",  # latin capital letter A with tilde
            "&Auml;": u"Ä",  # latin capital letter A with diaeresis
            "&Aring;": u"Å",  # latin capital letter A with ring above
            "&AElig;": u"Æ",  # latin capital letter AE
            "&Ccedil;": u"Ç",  # latin capital letter C with cedilla
            "&Egrave;": u"È",  # latin capital letter E with grave
            "&Eacute;": u"É",  # latin capital letter E with acute
            "&Ecirc;": u"Ê",  # latin capital letter E with circumflex
            "&Euml;": u"Ë",  # latin capital letter E with diaeresis
            "&Igrave;": u"Ì",  # latin capital letter I with grave
            "&Iacute;": u"Í",  # latin capital letter I with acute
            "&Icirc;": u"Î",  # latin capital letter I with circumflex
            "&Iuml;": u"Ï",  # latin capital letter I with diaeresis
            "&ETH;": u"Ð",  # latin capital letter ETH
            "&Ntilde;": u"Ñ",  # latin capital letter N with tilde
            "&Ograve;": u"Ò",  # latin capital letter O with grave
            "&Oacute;": u"Ó",  # latin capital letter O with acute
            "&Ocirc;": u"Ô",  # latin capital letter O with circumflex
            "&Otilde;": u"Õ",  # latin capital letter O with tilde
            "&Ouml;": u"Ö",  # latin capital letter O with diaeresis
            "&times;": u"×",  # multiplication sign
            "&Oslash;": u"Ø",  # latin capital letter O with slash
            "&Ugrave;": u"Ù",  # latin capital letter U with grave
            "&Uacute;": u"Ú",  # latin capital letter U with acute
            "&Ucirc;": u"Û",  # latin capital letter U with circumflex
            "&Uuml;": u"Ü",  # latin capital letter U with diaeresis
            "&Yacute;": u"Ý",  # latin capital letter Y with acute
            "&THORN;": u"Þ",  # latin capital letter THORN
            "&szlig;": u"ß",  # latin small letter sharp s - ess-zed
            "&agrave;": u"à",  # latin small letter a with grave
            "&aacute;": u"á",  # latin small letter a with acute
            "&acirc;": u"â",  # latin small letter a with circumflex
            "&atilde;": u"ã",  # latin small letter a with tilde
            "&auml;": u"ä",  # latin small letter a with diaeresis
            "&aring;": u"å",  # latin small letter a with ring above
            "&aelig;": u"æ",  # latin small letter ae
            "&ccedil;": u"ç",  # latin small letter c with cedilla
            "&egrave;": u"è",  # latin small letter e with grave
            "&eacute;": u"é",  # latin small letter e with acute
            "&ecirc;": u"ê",  # latin small letter e with circumflex
            "&euml;": u"ë",  # latin small letter e with diaeresis
            "&igrave;": u"ì",  # latin small letter i with grave
            "&iacute;": u"í",  # latin small letter i with acute
            "&icirc;": u"î",  # latin small letter i with circumflex
            "&iuml;": u"ï",  # latin small letter i with diaeresis
            "&eth;": u"ð",  # latin small letter eth
            "&ntilde;": u"ñ",  # latin small letter n with tilde
            "&ograve;": u"ò",  # latin small letter o with grave
            "&oacute;": u"ó",  # latin small letter o with acute
            "&ocirc;": u"ô",  # latin small letter o with circumflex
            "&otilde;": u"õ",  # latin small letter o with tilde
            "&ouml;": u"ö",  # latin small letter o with diaeresis
            "&divide;": u"÷",  # division sign
            "&oslash;": u"ø",  # latin small letter o with slash
            "&ugrave;": u"ù",  # latin small letter u with grave
            "&uacute;": u"ú",  # latin small letter u with acute
            "&ucirc;": u"û",  # latin small letter u with circumflex
            "&uuml;": u"ü",  # latin small letter u with diaeresis
            "&yacute;": u"ý",  # latin small letter y with acute
            "&thorn;": u"þ",  # latin small letter thorn
            "&yuml;": u"ÿ",  # latin small letter y with diaeresis
            "&euro;": u"€",  # euro sign
        }
        for e, v in chars.items():
            self.assertEqual(v, HtmlEntityHelper.convert_html_entities(e))

    def test_strip_amp(self):
        self.assertEqual("test&test", HtmlEntityHelper.strip_amp("test&amp;test"))
        self.assertEqual("test&test&", HtmlEntityHelper.strip_amp("test&amp;test&amp;"))
        self.assertEqual("test&", HtmlEntityHelper.strip_amp("test&amp;"))

    def test_convert_none(self):
        converted = HtmlEntityHelper.convert_html_entities(None)
        self.assertEqual(None, converted)

    def test_convert_error(self):
        converted = HtmlEntityHelper.convert_html_entities("&ampamp;")
        self.assertEqual("&ampamp;", converted)

    def test_urlencode(self):
        self.assertEqual("/%20connolly/", HtmlEntityHelper.url_encode("/ connolly/"))
        self.assertEqual("/ connolly/", HtmlEntityHelper.url_decode("/%20connolly/"))

    def test_urlencode_all(self):
        chars = [
            [" ", u" ", "%20", "%20"],
            ["!", u"!", "%21", "%21"],
            ["\"", u"\"", "%22", "%22"],
            ["#", u"#", "%23", "%23"],
            ["$", u"$", "%24", "%24"],
            ["%", u"%", "%25", "%25"],
            ["&", u"&", "%26", "%26"],
            ["'", u"'", "%27", "%27"],
            ["(", u"(", "%28", "%28"],
            [")", u")", "%29", "%29"],
            ["*", u"*", "%2A", "%2A"],
            ["+", u"+", "%2B", "%2B"],
            [",", u",", "%2C", "%2C"],
            # Not used in encoding
            # ["-", u"-", "%2D", "%2D"],
            # [".", u".", "%2E", "%2E"],
            # ["/", u"/", "%2F", "%2F"],
            # ["0", u"0", "%30", "%30"],
            # ["1", u"1", "%31", "%31"],
            # ["2", u"2", "%32", "%32"],
            # ["3", u"3", "%33", "%33"],
            # ["4", u"4", "%34", "%34"],
            # ["5", u"5", "%35", "%35"],
            # ["6", u"6", "%36", "%36"],
            # ["7", u"7", "%37", "%37"],
            # ["8", u"8", "%38", "%38"],
            # ["9", u"9", "%39", "%39"],
            [":", u":", "%3A", "%3A"],
            [";", u";", "%3B", "%3B"],
            ["<", u"<", "%3C", "%3C"],
            ["=", u"=", "%3D", "%3D"],
            [">", u">", "%3E", "%3E"],
            ["?", u"?", "%3F", "%3F"],
            ["@", u"@", "%40", "%40"],
            # Not used in encoding
            # ["A", u"A", "%41", "%41"],
            # ["B", u"B", "%42", "%42"],
            # ["C", u"C", "%43", "%43"],
            # ["D", u"D", "%44", "%44"],
            # ["E", u"E", "%45", "%45"],
            # ["F", u"F", "%46", "%46"],
            # ["G", u"G", "%47", "%47"],
            # ["H", u"H", "%48", "%48"],
            # ["I", u"I", "%49", "%49"],
            # ["J", u"J", "%4A", "%4A"],
            # ["K", u"K", "%4B", "%4B"],
            # ["L", u"L", "%4C", "%4C"],
            # ["M", u"M", "%4D", "%4D"],
            # ["N", u"N", "%4E", "%4E"],
            # ["O", u"O", "%4F", "%4F"],
            # ["P", u"P", "%50", "%50"],
            # ["Q", u"Q", "%51", "%51"],
            # ["R", u"R", "%52", "%52"],
            # ["S", u"S", "%53", "%53"],
            # ["T", u"T", "%54", "%54"],
            # ["U", u"U", "%55", "%55"],
            # ["V", u"V", "%56", "%56"],
            # ["W", u"W", "%57", "%57"],
            # ["X", u"X", "%58", "%58"],
            # ["Y", u"Y", "%59", "%59"],
            # ["Z", u"Z", "%5A", "%5A"],
            ["[", u"[", "%5B", "%5B"],
            ["\\", u"\\", "%5C", "%5C"],
            ["]", u"]", "%5D", "%5D"],
            ["^", u"^", "%5E", "%5E"],
            # ["_", u"_", "%5F", "%5F"],
            ["`", u"`", "%60", "%60"],
            # Not used in encoding
            # ["a", u"a", "%61", "%61"],
            # ["b", u"b", "%62", "%62"],
            # ["c", u"c", "%63", "%63"],
            # ["d", u"d", "%64", "%64"],
            # ["e", u"e", "%65", "%65"],
            # ["f", u"f", "%66", "%66"],
            # ["g", u"g", "%67", "%67"],
            # ["h", u"h", "%68", "%68"],
            # ["i", u"i", "%69", "%69"],
            # ["j", u"j", "%6A", "%6A"],
            # ["k", u"k", "%6B", "%6B"],
            # ["l", u"l", "%6C", "%6C"],
            # ["m", u"m", "%6D", "%6D"],
            # ["n", u"n", "%6E", "%6E"],
            # ["o", u"o", "%6F", "%6F"],
            # ["p", u"p", "%70", "%70"],
            # ["q", u"q", "%71", "%71"],
            # ["r", u"r", "%72", "%72"],
            # ["s", u"s", "%73", "%73"],
            # ["t", u"t", "%74", "%74"],
            # ["u", u"u", "%75", "%75"],
            # ["v", u"v", "%76", "%76"],
            # ["w", u"w", "%77", "%77"],
            # ["x", u"x", "%78", "%78"],
            # ["y", u"y", "%79", "%79"],
            # ["z", u"z", "%7A", "%7A"],
            ["{", u"{", "%7B", "%7B"],
            ["|", u"|", "%7C", "%7C"],
            ["}", u"}", "%7D", "%7D"],
            # Not used in encoding, is considere safe in Python 3
            # ["~", u"~", "%7E", "%7E"],
            # [" ", u" ", "%7F", "%7F"],
            # ["`", u"`", "%80", "%E2%82%AC"],
            # ["", u"", "%81", "%81"],
            # ["‚", u"‚", "%82", "%E2%80%9A"],
            ["ƒ", u"ƒ", "%83", "%C6%92"],
            ["„", u"„", "%84", "%E2%80%9E"],
            ["…", u"…", "%85", "%E2%80%A6"],
            ["†", u"†", "%86", "%E2%80%A0"],
            ["‡", u"‡", "%87", "%E2%80%A1"],
            ["ˆ", u"ˆ", "%88", "%CB%86"],
            ["‰", u"‰", "%89", "%E2%80%B0"],
            ["Š", u"Š", "%8A", "%C5%A0"],
            ["‹", u"‹", "%8B", "%E2%80%B9"],
            ["Œ", u"Œ", "%8C", "%C5%92"],
            # ["", u"", "%8D", "%C5%8D"],
            ["Ž", u"Ž", "%8E", "%C5%BD"],
            # is considere safe in Python 3
            # ["", u"", "%8F", "%8F"],
            # ["", u"", "%90", "%C2%90"],
            ["‘", u"‘", "%91", "%E2%80%98"],
            ["’", u"’", "%92", "%E2%80%99"],
            ["“", u"“", "%93", "%E2%80%9C"],
            ["”", u"”", "%94", "%E2%80%9D"],
            ["•", u"•", "%95", "%E2%80%A2"],
            ["–", u"–", "%96", "%E2%80%93"],
            ["—", u"—", "%97", "%E2%80%94"],
            ["˜", u"˜", "%98", "%CB%9C"],
            ["™", u"™", "%99", "%E2%84%A2"],
            ["š", u"š", "%9A", "%C5%A1"],
            ["›", u"›", "%9B", "%E2%80%BA"],
            ["œ", u"œ", "%9C", "%C5%93"],
            # ["", u"", "%9D", "%9D"],
            ["ž", u"ž", "%9E", "%C5%BE"],
            ["Ÿ", u"Ÿ", "%9F", "%C5%B8"],
            # [" ", u" ", "%A0", "%C2%A0"],
            ["¡", u"¡", "%A1", "%C2%A1"],
            ["¢", u"¢", "%A2", "%C2%A2"],
            ["£", u"£", "%A3", "%C2%A3"],
            ["¤", u"¤", "%A4", "%C2%A4"],
            ["¥", u"¥", "%A5", "%C2%A5"],
            ["¦", u"¦", "%A6", "%C2%A6"],
            ["§", u"§", "%A7", "%C2%A7"],
            ["¨", u"¨", "%A8", "%C2%A8"],
            ["©", u"©", "%A9", "%C2%A9"],
            ["ª", u"ª", "%AA", "%C2%AA"],
            ["«", u"«", "%AB", "%C2%AB"],
            ["¬", u"¬", "%AC", "%C2%AC"],
            ["­", u"­", "%AD", "%C2%AD"],
            ["®", u"®", "%AE", "%C2%AE"],
            ["¯", u"¯", "%AF", "%C2%AF"],
            ["°", u"°", "%B0", "%C2%B0"],
            ["±", u"±", "%B1", "%C2%B1"],
            ["²", u"²", "%B2", "%C2%B2"],
            ["³", u"³", "%B3", "%C2%B3"],
            ["´", u"´", "%B4", "%C2%B4"],
            ["µ", u"µ", "%B5", "%C2%B5"],
            ["¶", u"¶", "%B6", "%C2%B6"],
            ["·", u"·", "%B7", "%C2%B7"],
            ["¸", u"¸", "%B8", "%C2%B8"],
            ["¹", u"¹", "%B9", "%C2%B9"],
            ["º", u"º", "%BA", "%C2%BA"],
            ["»", u"»", "%BB", "%C2%BB"],
            ["¼", u"¼", "%BC", "%C2%BC"],
            ["½", u"½", "%BD", "%C2%BD"],
            ["¾", u"¾", "%BE", "%C2%BE"],
            ["¿", u"¿", "%BF", "%C2%BF"],
            ["À", u"À", "%C0", "%C3%80"],
            ["Á", u"Á", "%C1", "%C3%81"],
            ["Â", u"Â", "%C2", "%C3%82"],
            ["Ã", u"Ã", "%C3", "%C3%83"],
            ["Ä", u"Ä", "%C4", "%C3%84"],
            ["Å", u"Å", "%C5", "%C3%85"],
            ["Æ", u"Æ", "%C6", "%C3%86"],
            ["Ç", u"Ç", "%C7", "%C3%87"],
            ["È", u"È", "%C8", "%C3%88"],
            ["É", u"É", "%C9", "%C3%89"],
            ["Ê", u"Ê", "%CA", "%C3%8A"],
            ["Ë", u"Ë", "%CB", "%C3%8B"],
            ["Ì", u"Ì", "%CC", "%C3%8C"],
            ["Í", u"Í", "%CD", "%C3%8D"],
            ["Î", u"Î", "%CE", "%C3%8E"],
            ["Ï", u"Ï", "%CF", "%C3%8F"],
            ["Ð", u"Ð", "%D0", "%C3%90"],
            ["Ñ", u"Ñ", "%D1", "%C3%91"],
            ["Ò", u"Ò", "%D2", "%C3%92"],
            ["Ó", u"Ó", "%D3", "%C3%93"],
            ["Ô", u"Ô", "%D4", "%C3%94"],
            ["Õ", u"Õ", "%D5", "%C3%95"],
            ["Ö", u"Ö", "%D6", "%C3%96"],
            ["×", u"×", "%D7", "%C3%97"],
            ["Ø", u"Ø", "%D8", "%C3%98"],
            ["Ù", u"Ù", "%D9", "%C3%99"],
            ["Ú", u"Ú", "%DA", "%C3%9A"],
            ["Û", u"Û", "%DB", "%C3%9B"],
            ["Ü", u"Ü", "%DC", "%C3%9C"],
            ["Ý", u"Ý", "%DD", "%C3%9D"],
            ["Þ", u"Þ", "%DE", "%C3%9E"],
            ["ß", u"ß", "%DF", "%C3%9F"],
            ["à", u"à", "%E0", "%C3%A0"],
            ["á", u"á", "%E1", "%C3%A1"],
            ["â", u"â", "%E2", "%C3%A2"],
            ["ã", u"ã", "%E3", "%C3%A3"],
            ["ä", u"ä", "%E4", "%C3%A4"],
            ["å", u"å", "%E5", "%C3%A5"],
            ["æ", u"æ", "%E6", "%C3%A6"],
            ["ç", u"ç", "%E7", "%C3%A7"],
            ["è", u"è", "%E8", "%C3%A8"],
            ["é", u"é", "%E9", "%C3%A9"],
            ["ê", u"ê", "%EA", "%C3%AA"],
            ["ë", u"ë", "%EB", "%C3%AB"],
            ["ì", u"ì", "%EC", "%C3%AC"],
            ["í", u"í", "%ED", "%C3%AD"],
            ["î", u"î", "%EE", "%C3%AE"],
            ["ï", u"ï", "%EF", "%C3%AF"],
            ["ð", u"ð", "%F0", "%C3%B0"],
            ["ñ", u"ñ", "%F1", "%C3%B1"],
            ["ò", u"ò", "%F2", "%C3%B2"],
            ["ó", u"ó", "%F3", "%C3%B3"],
            ["ô", u"ô", "%F4", "%C3%B4"],
            ["õ", u"õ", "%F5", "%C3%B5"],
            ["ö", u"ö", "%F6", "%C3%B6"],
            ["÷", u"÷", "%F7", "%C3%B7"],
            ["ø", u"ø", "%F8", "%C3%B8"],
            ["ù", u"ù", "%F9", "%C3%B9"],
            ["ú", u"ú", "%FA", "%C3%BA"],
            ["û", u"û", "%FB", "%C3%BB"],
            ["ü", u"ü", "%FC", "%C3%BC"],
            ["ý", u"ý", "%FD", "%C3%BD"],
            ["þ", u"þ", "%FE", "%C3%BE"],
            ["ÿ", u"ÿ", "%FF", "%C3%BF"],
        ]

        for ascii_normal, uni_normal, ascii_encoded, uni_encoded in chars:
            print(ascii_normal, uni_normal, "->", ascii_encoded, uni_encoded)

            # Encoding should default to UTF8 encoding
            self.assertEqual(uni_encoded, HtmlEntityHelper.url_encode(ascii_normal))
            self.assertEqual(uni_encoded, HtmlEntityHelper.url_encode(uni_normal))
            # And decoding back from UTF8 encoded to ascii
            self.assertEqual(ascii_normal, HtmlEntityHelper.url_decode(uni_encoded))

    def test_basic_urlentities(self):
        pass
