# SPDX-License-Identifier: GPL-3.0-or-later


class AuthenticationResult:
    def __init__(self, username, has_premium=False, existing_login=False, uid=None, error=None):
        """ Log on result object

        :param str|None username:       The user name that is used for logging in.
        :param bool existing_login:     Indication whether the user was already logged in and this
                                         was just a the renew of the authentication session.
        :param bool has_premium:        Indication whether the user has a premium/paid account.
        :param str|None uid:            The internal user id for the username
        :param str|None error:          Error value

        """

        self.username = username
        self.logged_on = bool(username)
        self.existing_login = existing_login
        self.has_premium = has_premium
        self.uid = uid
        self.error = error

    def __str__(self):
        if not self.logged_on:
            return "Not logged on"

        return "Logged on with premium rights" if self.has_premium else "Logged on as normal user"
