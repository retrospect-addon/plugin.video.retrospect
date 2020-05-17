# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import json
import random

from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class GigyaHandler(AuthenticationHandler):
    def __init__(self, realm, api_key):
        """ Initializes a handler for the authentication provider

        :param str api_key:     The API key to use
        :param str realm:       The realm for this handler

        """

        if not api_key:
            raise ValueError("API Key required for Gigya")

        super(GigyaHandler, self).__init__(realm, device_id=None)

        self.api_key = api_key
        self.__setting_signature = "{}:signature".format(realm)

        # internal data
        self.__signature = None
        self.__user_id = None
        self.__signature_timestamp = None

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: a AuthenticationResult with the result of the log on
        :rtype: AuthenticationResult

        """

        common_data = "APIKey=%s&authMode=cookie" % (self.api_key,)

        # first we need a random context_id R<10 numbers>
        context_id = int(random.random() * 8999999999) + 1000000000

        # then we do an initial bootstrap call, which retrieves the `gmid` and `ucid` cookies
        url = "https://accounts.eu1.gigya.com/accounts.webSdkBootstrap?apiKey={}" \
              "&pageURL=https%3A%2F%2Fwatch.stievie.be%2F&format=jsonp" \
              "&callback=gigya.callback&context=R{}".format(self.api_key, context_id)
        init_login = UriHandler.open(url, no_cache=True)
        init_data = JsonHelper(init_login)
        if init_data.get_value("statusCode") != 200:
            Logger.error("Error initiating login")
            return AuthenticationResult(None)

        # actually do the login request, which requires an async call to retrieve the result
        login_url = "https://accounts.eu1.gigya.com/accounts.login" \
                    "?context={0}" \
                    "&saveResponseID=R{0}".format(context_id)
        login_data = "loginID=%s" \
                     "&password=%s" \
                     "&context=R%s" \
                     "&targetEnv=jssdk" \
                     "&sessionExpiration=-2" \
                     "&%s" % \
                     (HtmlEntityHelper.url_encode(username), HtmlEntityHelper.url_encode(password),
                      context_id, common_data)
        UriHandler.open(login_url, params=login_data, no_cache=True)

        #  retrieve the result
        login_retrieval_url = "https://accounts.eu1.gigya.com/socialize.getSavedResponse" \
                              "?APIKey={0}" \
                              "&saveResponseID=R{1}" \
                              "&noAuth=true" \
                              "&sdk=js_latest" \
                              "&format=json" \
                              "&context=R{1}".format(self.api_key, context_id)
        login_response = UriHandler.open(login_retrieval_url, no_cache=True)
        authentication_result = self.__extract_session_data(login_response)
        authentication_result.existing_login = False
        return authentication_result

    def active_authentication(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data.
        :rtype: AuthenticationResult

        """

        login_token = AddonSettings.get_setting(self.__setting_signature, store=LOCAL)
        common_data = "APIKey=%s&authMode=cookie" % (self.api_key,)

        login_cookie = UriHandler.get_cookie("gmid", domain=".gigya.com")
        if login_token and "|" \
                not in login_token and \
                login_cookie is not None and \
                not login_cookie.is_expired():
            # only retrieve the account information using the cookie and the token
            account_info_url = "https://accounts.eu1.gigya.com/accounts.getAccountInfo?{}" \
                               "&login_token={}".format(common_data, login_token)
            account_info = UriHandler.open(account_info_url, no_cache=True)

            # See if it was successfull
            auth_info = self.__extract_session_data(account_info)
            auth_info.existing_login = True
            return auth_info

        return AuthenticationResult(None)

    def get_authentication_token(self):
        raise NotImplementedError

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        raise NotImplementedError

    def __extract_session_data(self, logon_data):
        """

        :param logon_data:
        :return:
        :rtype: AuthenticationResult

        """

        logon_json = json.loads(logon_data)
        result_code = logon_json.get("statusCode")
        Logger.trace("Logging in returned: %s", result_code)
        if result_code != 200:
            Logger.error("Error loging in: %s - %s", logon_json.get("errorMessage"),
                         logon_json.get("errorDetails"))
            return AuthenticationResult(None)

        user_name = logon_json.get("profile", {}).get("email") or None

        signature_setting = logon_json.get("sessionInfo", {}).get("login_token")
        if signature_setting:
            Logger.info("Found 'login_token'. Saving it.")
            AddonSettings.set_setting(self.__setting_signature, signature_setting.split("|")[0], store=LOCAL)

        self.__signature = logon_json.get("UIDSignature")
        self.__user_id = logon_json.get("UID")
        self.__signature_timestamp = logon_json.get("signatureTimestamp")

        has_premium = logon_json.get(
            "data", {}).get("authorization", {}).get("Stievie_free", {}).get("subscription", {}).get("id") == "premium"

        # The channels are not interesting
        # premium_channels = logon_json.get_value(
        #     "data", "authorization", "Stievie_free", "channels")
        return AuthenticationResult(user_name, has_premium=has_premium)
