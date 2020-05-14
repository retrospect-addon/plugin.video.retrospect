# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import binascii
import os
import pyaes
import random
import time
import json

from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


class ArkoseHandler(AuthenticationHandler):
    def __init__(self, realm, device_id):
        """ Initializes a handler for the authentication provider

        :param str realm:
        :param str device_id:

        """

        device_id = device_id.lower().replace("-", "")

        if len(device_id) != 32:
            raise ValueError("Invalid Device ID. Must be length 32 without dashes and lowercase.")

        super(ArkoseHandler, self).__init__(realm, device_id)

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: An indication of a successful login.
        :rtype: bool

        """

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
        window_id = "{}|{}".format(
            binascii.hexlify(os.urandom(16)).decode(),
            binascii.hexlify(os.urandom(16)).decode()
        ).lower()

        now = int(time.time())
        b64_now = binascii.b2a_base64(str(now).encode()).decode().strip()
        stamp = now - (now % (60*60*6))
        key_password = "{}{}".format(user_agent, stamp)

        # region Browser properties seem optional
        # fe = [
        #     "DNT:1",
        #     "L:en-NL",
        #     "D:24",
        #     "PR:1",
        #     "S:1920,1080",
        #     "AS:1920,1040",
        #     "TO:-120",
        #     "SS:true",
        #     "LS:true",
        #     "IDB:true",
        #     "B:false",
        #     "ODB:true",
        #     "CPUC:unknown",
        #     "PK:Win32",
        #     "CFP:-1424337346",
        #     "FR:false",
        #     "FOS:false",
        #     "FB:false",
        #     "JSF:Arial,Arial Black,Arial Narrow,Book Antiqua,Bookman Old Style,Calibri,Cambria,Cambria Math,Century,Century Gothic,Century Schoolbook,Comic Sans MS,Consolas,Courier,Courier New,Garamond,Georgia,Helvetica,Impact,Lucida Bright,Lucida Calligraphy,Lucida Console,Lucida Fax,Lucida Handwriting,Lucida Sans,Lucida Sans Typewriter,Lucida Sans Unicode,Microsoft Sans Serif,Monotype Corsiva,MS Gothic,MS PGothic,MS Reference Sans Serif,MS Sans Serif,MS Serif,Palatino Linotype,Segoe Print,Segoe Script,Segoe UI,Segoe UI Light,Segoe UI Semibold,Segoe UI Symbol,Tahoma,Times,Times New Roman,Trebuchet MS,Verdana,Wingdings,Wingdings 2,Wingdings 3",
        #     "P:Chrome PDF Plugin,Chrome PDF Viewer,Native Client",
        #     "T:1,false,false",
        #     "H:12",
        #     "SWF:false"
        # ]
        # fs_murmur_value = ", ".join(fe)
        # # Murmur (x64 128-bit) from fs_murmur_value via https://asecuritysite.com/encryption/mur
        # fs_murmur = "0xfa204e6c7927d156f9b50d837b6cb295L"
        # fs_murmur_hash = self.__transform_murmur(fs_murmur)
        # endregion

        data = [
            {"key": "api_type", "value": "js"},
            {"key": "p", "value": 1},  # constant
            {"key": "f", "value": self._device_id},  # browser instance ID
            {"key": "n", "value": b64_now},  # base64 encoding of time.now()
            {"key": "wh", "value": window_id},  # WindowHandle ID
            # {"key": "fe", "value": fe},                     # browser properties
            # {"key": "ife_hash", "value": fs_murmur_hash},   # hash of browser properties
            {"key": "cs", "value": 1},  # canvas supported 0/1
            {"key": "jsbd", "value": "{\"HL\":41,\"NCE\":true,\"DMTO\":1,\"DOTO\":1}"}
        ]
        # Use native json to prevent any issues with JsonHelper
        data_value = json.dumps(data)

        # Initialize the encryption parameters
        salt_bytes = os.urandom(8)
        key_iv = self.__evp_kdf(key_password.encode(), salt_bytes,
                                key_size=8, iv_size=4, iterations=1, hash_algorithm="md5")
        key = key_iv["key"]
        iv = key_iv["iv"]

        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        encrypted = encrypter.feed(data_value)
        # Again, make a final call to flush any remaining bytes and strip padding
        encrypted += encrypter.feed()

        salt_hex = binascii.hexlify(salt_bytes)
        iv_hex = binascii.hexlify(iv)
        encrypted_b64 = binascii.b2a_base64(encrypted)
        bda = {
            "ct": encrypted_b64.decode().rstrip(),
            "iv": iv_hex.decode().lower(),
            "s": salt_hex.decode().lower()
        }
        bda_str = json.dumps(bda)
        bda_base64 = binascii.b2a_base64(bda_str.encode())

        # Create the main request parameters
        req_dict = {
            "bda": bda_base64.decode().strip(),
            "public_key": "FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            "site": "https://client-api.arkoselabs.com",
            "userbrowser": user_agent,
            "simulate_rate_limit": "0",
            "simulated": "0",
            "rnd": "{}".format(random.random())
        }
        req_data = ""
        for k, v in req_dict.items():
            req_data = "{}{}={}&".format(req_data, k, HtmlEntityHelper.url_encode(v))
        req_data = req_data.rstrip("&")

        # Make a call to Arkose
        arkose_data = UriHandler.open(
            "https://client-api.arkoselabs.com/fc/gt2/public_key/FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            data=req_data,
            additional_headers={"user-agent": user_agent}, no_cache=True
        )
        arkose_json = JsonHelper(arkose_data)
        arkose_token = arkose_json.get_value("token")
        if "rid=" not in arkose_token:
            Logger.error("Error logging in. Invalid Arkose token.")
            return False
        Logger.debug("Succesfully required a login token from Arkose.")

        # New we need to access the API of Dplay for logging in
        UriHandler.open(
            "https://disco-api.dplay.se/token?realm=dplayse&deviceId={}&shortlived=true".format(
                self._device_id),
            no_cache=True
        )

        # Do the actual call for login
        creds = {"credentials": {"username": username, "password": password}}
        headers = {
            "x-disco-arkose-token": arkose_token,
            "Origin": "https://auth.dplay.se",
            "x-disco-client": "WEB:10:AUTH_DPLAY_V1:2.4.1",
            # is not specified a captcha is required
            # "Sec-Fetch-Site": "same-site",
            # "Sec-Fetch-Mode": "cors",
            # "Sec-Fetch-Dest": "empty",
            "Referer": "https://auth.dplay.se/login",
            "User-Agent": user_agent
        }
        result = UriHandler.open("https://disco-api.dplay.se/login",
                                 json=creds, additional_headers=headers)
        if UriHandler.instance().status.code > 299:
            Logger.error("Failed to log in: %s", result)
            return False

        Logger.debug("Succesfully logged in")
        return True

    def is_authenticated(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username

        """

        UriHandler.open(
            "https://disco-api.dplay.se/token?realm=dplayse&deviceId={}&shortlived=true"
            .format(self._device_id), no_cache=True
        )

        me = UriHandler.open("https://disco-api.dplay.se/users/me", no_cache=True)
        if UriHandler.instance().status.code >= 300:
            return False

        account_data = JsonHelper(me)
        signed_in_user = account_data.get_value("data", "attributes", "username")
        return signed_in_user == username

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        UriHandler.open("https://disco-api.dplay.se/logout", data="", no_cache=True)
        return 200 <= UriHandler.instance().status.code <= 210

    def __evp_kdf(self, passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
        """
        https://gist.github.com/adrianlzt/d5c9657e205b57f687f528a5ac59fe0e

        https://github.com/Shani-08/ShaniXBMCWork2/blob/master/plugin.video.serialzone/jscrypto.py

        :param byte passwd:
        :param byte salt:
        :param int key_size:
        :param int iv_size:
        :param int iterations:
        :param str hash_algorithm:

        :return:

        """

        import hashlib

        target_key_size = key_size + iv_size
        derived_bytes = b""
        number_of_derived_words = 0
        block = None
        hasher = hashlib.new(hash_algorithm)

        while number_of_derived_words < target_key_size:
            if block is not None:
                hasher.update(block)

            hasher.update(passwd)
            hasher.update(salt)
            block = hasher.digest()

            hasher = hashlib.new(hash_algorithm)

            for _ in range(1, iterations):
                hasher.update(block)
                block = hasher.digest()
                hasher = hashlib.new(hash_algorithm)

            derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

            number_of_derived_words += len(block)/4

        return {
            "key": derived_bytes[0: key_size * 4],
            "iv": derived_bytes[key_size * 4:]
        }
