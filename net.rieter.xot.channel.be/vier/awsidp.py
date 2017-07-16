import base64
import hashlib
import hmac
import os
import binascii
import sys

import datetime

from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


class AwsIdp:
    def __init__(self, pool_id, client_id, proxy=None, logger=None):
        """ Simple AWS Identity Provider client.

        @param pool_id:     [str] the AWS user pool to connect to (format: <region>_<poolid>).
                            E.g.: eu-west-1_aLkOfYN3T
        @param client_id:   [str] the client application ID (the ID of the application connecting)
        @param proxy:       [ProxyInfo] a proxy info object if needed

        The content of this file is a simplification of the Warrent aws_srp.py file.

        """

        self.pool_id = pool_id
        if "_" not in self.pool_id:
            raise ValueError("Invalid pool_id format. Shoud be <region>_<poolid>.")

        self.client_id = client_id
        self.region = self.pool_id.split("_")[0]
        self.url = "https://cognito-idp.%s.amazonaws.com/" % (self.region, )
        self.__proxy = proxy
        self.__logger = logger

        # Initialize the values
        # https://github.com/aws/amazon-cognito-identity-js/blob/master/src/AuthenticationHelper.js#L22
        self.n_hex = 'FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1' + \
                     '29024E088A67CC74020BBEA63B139B22514A08798E3404DD' + \
                     'EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245' + \
                     'E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED' + \
                     'EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D' + \
                     'C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F' + \
                     '83655D23DCA3AD961C62F356208552BB9ED529077096966D' + \
                     '670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B' + \
                     'E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9' + \
                     'DE2BCBF6955817183995497CEA956AE515D2261898FA0510' + \
                     '15728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64' + \
                     'ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7' + \
                     'ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6B' + \
                     'F12FFA06D98A0864D87602733EC86A64521F2B18177B200C' + \
                     'BBE117577A615D6C770988C0BAD946E208E24FA074E5AB31' + \
                     '43DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF'

        # https://github.com/aws/amazon-cognito-identity-js/blob/master/src/AuthenticationHelper.js#L49
        self.g_hex = '2'
        self.info_bits = bytearray('Caldera Derived Key', 'utf-8')

        self.big_n = self.__HexToLong(self.n_hex)
        self.g = self.__HexToLong(self.g_hex)
        self.k = self.__HexToLong(self.__HexHash('00' + self.n_hex + '0' + self.g_hex))
        self.small_a_value = self.__GenerateRandomSmallA()
        self.large_a_value = self.__CalculateA()
        if self.__logger:
            self.__logger.Debug("Created %s", self)

    def Authenticate(self, username, password):
        # Step 1: First initiate an authentication request
        authRequest = self.__GetAuthenticationRequest(username)
        authData = JsonHelper.Dump(authRequest)
        authHeaders = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Accept-Encoding": "identity",
            "Content-Type": "application/x-amz-json-1.1"
        }
        authResponse = UriHandler.Open(self.url, proxy=self.__proxy,
                                       params=authData, additionalHeaders=authHeaders)
        authResponseJson = JsonHelper(authResponse)
        challengeParameters = authResponseJson.GetValue("ChallengeParameters")
        if self.__logger:
            self.__logger.Trace(challengeParameters)

        challengeName = authResponseJson.GetValue("ChallengeName")
        if not challengeName == "PASSWORD_VERIFIER":
            if self.__logger:
                self.__logger.Error("Cannot start authentication challenge")
                return None

        # Step 2: Respond to the Challenge with a valid ChallengeResponse
        challengeRequest = self.__GetChallengeResponseRequest(challengeParameters, password)
        challengeData = JsonHelper.Dump(challengeRequest)
        challengeHeaders = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.RespondToAuthChallenge",
            "Content-Type": "application/x-amz-json-1.1"
        }
        authResponse = UriHandler.Open(self.url, proxy=self.__proxy,
                                       params=challengeData, additionalHeaders=challengeHeaders)
        # if not authResponse:
        #     raise ValueError("No data on ChallengeResponse. Wrong username/password?")

        authResponseJson = JsonHelper(authResponse)
        if "message" in authResponseJson.json:
            raise ValueError(authResponseJson.GetValue("message"))

        idToken = authResponseJson.GetValue("AuthenticationResult", "IdToken")
        refreshToken = authResponseJson.GetValue("AuthenticationResult", "RefreshToken")
        return idToken, refreshToken

    def RenewToken(self, refreshToken):
        """
        Sets a new access token on the User using the refresh token. The basic expire time of the
        refresh token is 30 days:

        http://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html

        """

        refreshRequest = {
            "AuthParameters": {
                "REFRESH_TOKEN": refreshToken
            },
            "ClientId": self.client_id,
            "AuthFlow": "REFRESH_TOKEN"
        }
        refreshHeaders = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1"
        }
        refreshRequestData = JsonHelper.Dump(refreshRequest)
        refreshResponse = UriHandler.Open(self.url, proxy=self.__proxy,
                                          params=refreshRequestData,
                                          additionalHeaders=refreshHeaders)
        refreshJson = JsonHelper(refreshResponse)
        idToken = refreshJson.GetValue("AuthenticationResult", "IdToken")
        return idToken

    def __GetAuthenticationRequest(self, username):
        authRequest = {
            "AuthParameters": {
                "USERNAME": username,
                "SRP_A": self.__LongToHex(self.large_a_value)
            },
            "AuthFlow": "USER_SRP_AUTH",
            "ClientId": self.client_id
        }
        return authRequest

    def __GetChallengeResponseRequest(self, challengeParameters, password):
        userId = challengeParameters["USERNAME"]
        userIdForSrp = challengeParameters["USER_ID_FOR_SRP"]
        srpB = challengeParameters["SRP_B"]
        salt = challengeParameters["SALT"]
        secretBlock = challengeParameters["SECRET_BLOCK"]

        if sys.platform.startswith('win'):
            format_string = "%a %b %#d %H:%M:%S UTC %Y"
        else:
            format_string = "%a %b %-d %H:%M:%S UTC %Y"
        timestamp = datetime.datetime.utcnow().strftime(format_string)

        # Get a HKDF key for the password, SrpB and the Salt
        hkdf = self.__GetHkdfKeyForPassword(
            userIdForSrp,
            password,
            self.__HexToLong(srpB),
            salt
        )
        secret_block_bytes = base64.standard_b64decode(secretBlock)

        # the message is a combo of the pool_id, provided SRP userId, the Secret and Timestamp
        msg = bytearray(self.pool_id.split('_')[1], 'utf-8') + \
            bytearray(userIdForSrp, 'utf-8') + \
            bytearray(secret_block_bytes) + \
            bytearray(timestamp, 'utf-8')
        hmac_obj = hmac.new(hkdf, msg, digestmod=hashlib.sha256)
        signature_string = base64.standard_b64encode(hmac_obj.digest())
        challengeRequest = {
            "ChallengeResponses": {
                "USERNAME": userId,
                "TIMESTAMP": timestamp,
                "PASSWORD_CLAIM_SECRET_BLOCK": secretBlock,
                "PASSWORD_CLAIM_SIGNATURE": signature_string
            },
            "ChallengeName": "PASSWORD_VERIFIER",
            "ClientId": self.client_id
        }
        return challengeRequest

    def __GetHkdfKeyForPassword(self, username, password, server_b_value, salt):
        """
        Calculates the final hkdf based on computed S value, and computed U value and the key
        :param {String} username Username.
        :param {String} password Password.
        :param {Long integer} server_b_value Server B value.
        :param {Long integer} salt Generated salt.
        :return {Buffer} Computed HKDF value.
        """
        u_value = self.__CalculateU(self.large_a_value, server_b_value)
        if u_value == 0:
            raise ValueError('U cannot be zero.')
        username_password = '%s%s:%s' % (self.pool_id.split('_')[1], username, password)
        username_password_hash = self.__HashSha256(username_password.encode('utf-8'))

        x_value = self.__HexToLong(self.__HexHash(self.__PadHex(salt) + username_password_hash))
        g_mod_pow_xn = pow(self.g, x_value, self.big_n)
        int_value2 = server_b_value - self.k * g_mod_pow_xn
        s_value = pow(int_value2, self.small_a_value + u_value * x_value, self.big_n)
        hkdf = self.__ComputeHkdf(
            bytearray.fromhex(self.__PadHex(s_value)),
            bytearray.fromhex(self.__PadHex(self.__LongToHex(u_value)))
        )
        return hkdf

    def __ComputeHkdf(self, ikm, salt):
        """
        Standard hkdf algorithm
        :param {Buffer} ikm Input key material.
        :param {Buffer} salt Salt value.
        :return {Buffer} Strong key material.
        @private
        """
        prk = hmac.new(salt, ikm, hashlib.sha256).digest()
        info_bits_update = self.info_bits + bytearray(chr(1), 'utf-8')
        hmac_hash = hmac.new(prk, info_bits_update, hashlib.sha256).digest()
        return hmac_hash[:16]

    def __CalculateU(self, big_a, big_b):
        """
        Calculate the client's value U which is the hash of A and B
        :param {Long integer} big_a Large A value.
        :param {Long integer} big_b Server B value.
        :return {Long integer} Computed U value.
        """
        u_hex_hash = self.__HexHash(self.__PadHex(big_a) + self.__PadHex(big_b))
        return self.__HexToLong(u_hex_hash)

    def __GenerateRandomSmallA(self):
        """
        helper function to generate a random big integer
        :return {Long integer} a random value.
        """
        random_long_int = self.__GetRandom(128)
        return random_long_int % self.big_n

    def __CalculateA(self):
        """
        Calculate the client's public value A = g^a%N
        with the generated random number a
        :param {Long integer} a Randomly generated small A.
        :return {Long integer} Computed large A.
        """
        big_a = pow(self.g, self.small_a_value, self.big_n)
        # safety check
        if (big_a % self.big_n) == 0:
            raise ValueError('Safety check for A failed')
        return big_a

    @staticmethod
    def __LongToHex(long_num):
        return '%x' % long_num

    @staticmethod
    def __HexToLong(hex_string):
        return int(hex_string, 16)

    @staticmethod
    def __HexHash(hex_string):
        return AwsIdp.__HashSha256(bytearray.fromhex(hex_string))

    @staticmethod
    def __HashSha256(buf):
        """AuthenticationHelper.hash"""
        a = hashlib.sha256(buf).hexdigest()
        return (64 - len(a)) * '0' + a

    @staticmethod
    def __PadHex(long_int):
        """
        Converts a Long integer (or hex string) to hex format padded with zeroes for hashing
        :param {Long integer|String} long_int Number or string to pad.
        :return {String} Padded hex string.
        """

        # noinspection PyTypeChecker
        if not isinstance(long_int, basestring):
            hashStr = AwsIdp.__LongToHex(long_int)
        else:
            hashStr = long_int
        if len(hashStr) % 2 == 1:
            hashStr = '0%s' % hashStr
        elif hashStr[0] in '89ABCDEFabcdef':
            hashStr = '00%s' % hashStr
        return hashStr

    @staticmethod
    def __GetRandom(nbytes):
        random_hex = binascii.hexlify(os.urandom(nbytes))
        return AwsIdp.__HexToLong(random_hex)

    def __str__(self):
        return "AWS IDP Client for:\nRegion: %s\nPoolId: %s\nAppId:  %s" % (
            self.region, self.pool_id.split("_")[1], self.client_id
        )
