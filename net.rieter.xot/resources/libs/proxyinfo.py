#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import urllib2


class ProxyInfo:
    def __init__(self, proxy, port, scheme="http", username="", password=""):
        """ Retrieves a new ProxyInfo object

        Arguments:
        proxy:    String - Name or IP of the Proxy server
        port:     Int    - The port of the proxy server

        Keyword Arguments:
        scheme:   String - [opt] The type of proxy (http is default)
        username: String - [opt] The username to use (if empty or ommitted no
                           authentication is done.
        password: String - [opt] The password to use.

        """

        self.Proxy = proxy
        self.Port = int(port)
        self.Scheme = scheme
        self.Username = username
        self.Password = password
        self.Filter = []            # : If specified, only URLs that contain these parts will be routed via the proxy.

    def GetSmartProxyHandler(self, scheme=None):
        """ Gets a Proxy Handler  based on the settings

        Keyword Arguments:
        scheme : String - Can be used to override the scheme

        """

        if self.Proxy == "":
            proxyHandler = urllib2.ProxyHandler({})
        else:
            address = self.GetProxyAddress()
            proxyHandler = urllib2.ProxyHandler({scheme or self.Scheme: address})

        return proxyHandler

    def GetProxyAddress(self, hidePassword=False):
        """ Returns the proxy address for this proxy

        Keyword Arguments:
        hidePassword : Boolean - Should we show or hide the password

        """

        if self.Scheme.lower() == "dns":
            return "%s://%s" % (self.Scheme, self.Proxy)

        elif self.__IsSecure():
            if hidePassword:
                return "%s://%s:*******@%s:%s" % (self.Scheme, self.Username, self.Proxy, self.Port)
            else:
                return "%s://%s:%s@%s:%s" % (self.Scheme, self.Username, self.Password, self.Proxy, self.Port)
        else:
            return "%s://%s:%s" % (self.Scheme, self.Proxy, self.Port)

    def UseProxyForUrl(self, url):
        """ Checks whether the URL is allowed based on the proxy filter

        Arguments:
        url : String - The URL

        """
        if not self.Filter:
            return True

        # if any word in the filterlist appears in the url, use the proxy
        return any(f in url for f in self.Filter)

    def __IsSecure(self):
        """ An easy way of determining if this server should use proxy authentication."""

        return not self.Username == ""

    def __str__(self):
        """ returns a string representation """

        if self.Proxy == "":
            return "Proxy Default Override."

        return "Proxy (%s): %s" % (self.Scheme, self.GetProxyAddress(True))
