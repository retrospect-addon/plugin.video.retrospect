# SPDX-License-Identifier: CC-BY-NC-SA-4.0


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

        :returns: An indication of a successful login.
        :rtype: bool

        """
        raise NotImplementedError

    def is_authenticated(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username

        """

        raise NotImplementedError

    def log_off(self, username):
        """ Check if the user with the given name is currently authenticated.

        :param str username:    The username to log off

        :returns: Indication of success
        :rtype: bool

        """

        raise NotImplementedError
