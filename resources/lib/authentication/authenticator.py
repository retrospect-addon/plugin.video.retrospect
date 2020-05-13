# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from .authenticationhandler import AuthenticationHandler


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
        :rtype: bool

        """

        raise NotImplementedError

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        """

        raise NotImplementedError
