# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from .authenticationhandler import AuthenticationHandler
from .authenticationresult import AuthenticationResult
from ..logger import Logger


class Authenticator(object):
    def __init__(self, handler):
        """ Main logic handler for authentication.

        :param AuthenticationHandler handler:   The authentication handler to use.

        """

        if handler is None:
            raise ValueError("No authenication handler specified.")

        if not isinstance(handler, AuthenticationHandler):
            raise ValueError("Invalid authenication handler specified.")

        self.__hander = handler

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: An indication of a successful login.
        :rtype: AuthenticationResult

        """

        if not username or not password:
            raise ValueError("No username and/or password specified")

        res = self.__hander.active_authentication()
        logged_on_user = res.username

        # Check if existing ones
        if logged_on_user and logged_on_user != username:
            Logger.warning("Existing but different authenticated user (%s) found. Logging of first.",
                           self.__safe_log(logged_on_user))
            self.__hander.log_off(logged_on_user)

        elif logged_on_user and logged_on_user == username:
            Logger.warning("Existing authenticated user (%s) found.", self.__safe_log(logged_on_user))
            return res

        Logger.warning("Logging on user: %s", self.__safe_log(username))
        res = self.__hander.log_on(username, password)
        return res

    def active_authentication(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data
        :rtype: AuthenticationResult

        """

        return self.__hander.active_authentication()

    def log_off(self, username, force=True):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        """

        res = self.__hander.active_authentication()
        if not res.logged_on:
            Logger.debug("User was not logged on.")
            return

        logged_on_user = res.username
        if logged_on_user is not None and (force or logged_on_user == username):
            res = self.__hander.log_off(logged_on_user)
            if res:
                Logger.debug("Logged off successfully")
            else:
                Logger.error("Log off failed")

    def __safe_log(self, text):
        return "".join([text[i] if i % 2 == 0 else "*" for i in range(0, len(text))])
