#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import base64

# prefer hashlib over md5. But XBMC4Xbox does not have hashlib, so fallback to
# md5 if an import error occurs.
try:
    import hashlib
except:
    # noinspection PyDeprecation
    import md5


class EncodingHelper:
    """Class that is intended to help with the encoding and decoding
    of text.

    """

    def __init__(self):
        """Initialises the class with a text-encoder and -decoder.

        Python explanation of text encoding and decoding:

        s.decode(encoding)
            * <type 'str'> to <type 'unicode'>
        u.encode(encoding)
            * <type 'unicode'> to <type 'str'> (or Binary data)

        """
        #codecs.register_error('keep', EncodingHelper.__KeepHandler)
        #self.decoder = decoder
        #self.encoder = encoder
        return

    @staticmethod
    def DecodeBase64(data):
        """Decodes a Base64 encoded string into a normal string.

        Arguments:
        data : Base64 encode string - data to decode.

        Returns:
        Normal string representing the Base64 encoded string.

        """

        return base64.b64decode(data)

    @staticmethod
    def EncodeMD5(data, toUpper=True):
        """Encodes the selected string into an MD5 hashTool.

        Arguments:
        data : string - data for which the MD5 should be calculated.

        Keyword Arguments:
        toUpper : [opt] boolean : result should be upper-case. (default: True)

        """

        try:
            hashTool = hashlib.md5()    # @UndefinedVariable
        except:
            # noinspection PyDeprecation
            hashTool = md5.new()

        hashTool.update(data)
        if toUpper:
            return hashTool.hexdigest().upper()
        else:
            return hashTool.hexdigest()

    @staticmethod
    def __KeepHandler(exc):
        """Sometimes the unicode decoding fails due to strange UTF-8 chars in
        string that should not be there. This method just converts the chars
        in the string to Unicode chars and then returns the as their unicode
        chars.

        Arguments:
        exc : UnicodeDecodeError - Excpetion thrown by Decode.


        Returns the same as the input but then Unicode:
        'Barnen p\xe5 Luna p\xe5 Svt.se' returns u'Barnen p\xe5 Luna p\xe5 Svt.se'

        """

        try:
            returnValue = u''
            for c in exc.object[exc.start:exc.end]:
                # just convert each character as if it was Unicode to it's Unicode equivalent.
                returnValue = u'%s%s' % (returnValue, unichr(ord(c)))
        except:
            returnValue = exc.object[exc.start:exc.end].decode(exc.encoding, 'replace')
        return returnValue, exc.end
