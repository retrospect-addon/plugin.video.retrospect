# SPDX-License-Identifier: CC-BY-NC-SA-4.0


class AuthenticationResult:
    def __init__(self, username, has_premium=False, existing_login=False):
        """ Log on result object

        :param str|None username:
        :param bool existing_login:
        :param bool has_premium:

        """

        self.username = username
        self.logged_on = bool(username)
        self.existing_login = existing_login
        self.has_premium = has_premium

    def __str__(self):
        if not self.logged_on:
            return "Not logged on"

        return "Logged on with premium rights" if self.has_premium else "Logged on as normal user"
