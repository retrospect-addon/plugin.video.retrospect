# SPDX-License-Identifier: CC-BY-NC-SA-4.0


class AuthenticationResult:
    def __init__(self, logged_on, has_premium=False):
        """ Log on result object

        :param bool logged_on:
        :param bool has_premium:

        """

        self.logged_on = logged_on
        self.has_premium = has_premium
