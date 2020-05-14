# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.authentication.authenticationresult import AuthenticationResult


class AuthenticationHandler(object):
    def __init__(self, realm, device_id):
        """ Initializes a handler for the authentication provider

        :param str realm:
        :param str device_id:

        """

        if not realm:
            raise ValueError("Missing 'realm' initializer.")

        self._device_id = device_id
        self._realm = realm
        return

    @property
    def domain(self):
        return self._realm

    def log_on(self, username, password):
        """ Peforms the logon of a user.

        :param str username:    The username
        :param str password:    The password to use

        :returns: a AuthenticationResult with the result of the log on
        :rtype: AuthenticationResult

        """
        raise NotImplementedError

    def authenticated_user(self):
        """ Check if the user with the given name is currently authenticated.

        :returns: a AuthenticationResult with the account data
        :rtype: str

        """

        raise NotImplementedError

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        raise NotImplementedError
