# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import json

from resources.lib.authentication.authenticationhandler import AuthenticationHandler
from resources.lib.authentication.authenticationresult import AuthenticationResult
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.urihandler import UriHandler


class NpoHandler(AuthenticationHandler):
    def __init__(self, realm):
        """ Initializes a handler for the authentication provider

        :param str realm:

        """

        super(NpoHandler, self).__init__(realm, device_id=None)

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: a AuthenticationResult with the result of the log on
        :rtype: AuthenticationResult

        """

        xsrf_token = self.__get_xsrf_token()
        if not xsrf_token:
            return False

        data = "username=%s&password=%s" % (HtmlEntityHelper.url_encode(username),
                                            HtmlEntityHelper.url_encode(password))
        UriHandler.open("https://www.npostart.nl/api/login", no_cache=True,
                        additional_headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "X-XSRF-TOKEN": xsrf_token
                        },
                        params=data)

        authenticate_cookie = UriHandler.get_cookie('isAuthenticatedUser', "www.npostart.nl")
        if not authenticate_cookie or authenticate_cookie.value != "1":
            return AuthenticationResult(False)

        subscription_cookie = UriHandler.get_cookie("subscription", "www.npostart.nl")
        has_premium = False
        if subscription_cookie:
            has_premium = subscription_cookie.value == "npoplus"

        success = not UriHandler.instance().status.error
        if success:
            self._store_current_user_in_settings(username)
        return AuthenticationResult(success, has_premium)

    def authenticated_user(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data
        :rtype: str

        """

        # Check for a cookie as the first check
        authenticate_cookie = UriHandler.get_cookie('isAuthenticatedUser', "www.npostart.nl")
        if not authenticate_cookie or \
                authenticate_cookie.is_expired() or \
                authenticate_cookie.value != "1":
            self._store_current_user_in_settings(None)
            return None

        # See if we can retrieve our profile
        xsrf_token = self.__get_xsrf_token()
        # Check to see if we are still logged on.
        UriHandler.open(
            "https://www.npostart.nl/api/account/@me",
            additional_headers={
                "X-Requested-With": "XMLHttpRequest",
                "X-XSRF-TOKEN": xsrf_token
            }
        )

        if UriHandler.instance().status.error:
            # Not logged on anymore
            self._store_current_user_in_settings(None)
            return None

        return self._get_current_user_in_settings()

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        # Clearing cookies seems sufficient
        # xsrf_token = self.__get_xsrf_token()
        # # Check to see if we are still logged on.
        # UriHandler.open(
        #     "https://www.npostart.nl/logout",
        #     additional_headers={
        #         "X-Requested-With": "XMLHttpRequest",
        #         "X-XSRF-TOKEN": xsrf_token
        #     },
        #     data=""
        # )
        #
        UriHandler.delete_cookie(domain="www.npostart.nl")
        UriHandler.delete_cookie(domain=".npostart.nl")

        self._store_current_user_in_settings(None)
        return True

    def __get_xsrf_token(self):
        """ Retrieves a JSON Token and XSRF token

        :return: XSRF Token and JSON Token
        :rtype: tuple[str|None,str|None]
        """

        # get a token (why?), cookies and an xsrf token
        token = UriHandler.open("https://www.npostart.nl/api/token", no_cache=True,
                                additional_headers={"X-Requested-With": "XMLHttpRequest"})

        token_data = json.loads(token)
        token = token_data.get("token")
        if not token:
            return None

        xsrf_token = UriHandler.get_cookie("XSRF-TOKEN", "www.npostart.nl").value
        xsrf_token = HtmlEntityHelper.url_decode(xsrf_token)
        return xsrf_token
