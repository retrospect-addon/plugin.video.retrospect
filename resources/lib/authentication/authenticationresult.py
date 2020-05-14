# SPDX-License-Identifier: CC-BY-NC-SA-4.0


class AuthenticationResult:
    def __init__(self, logged_on, has_premium=False):
        """ Log on result object

        :param bool logged_on:
        :param bool has_premium:

        """

        self.logged_on = logged_on
        self.has_premium = has_premium

    def __str__(self):
        if not self.logged_on:
            return "Not logged on"

        return "Logged on with premium rights" if self.has_premium else "Logged on as normal user"
