#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
from logger import Logger
from urihandler import UriHandler
from proxyinfo import ProxyInfo

__author__ = 'Bas Rieter'


class DebugInitializer:
    Proxy = None

    def __init__(self):
        """ Simply initializes some default debugging objects such as loggers, urihandlers and a proxy """

        # noinspection PyUnusedLocal
        def __DualLog(msg, level):
            print msg

        DebugInitializer.Proxy = ProxyInfo("localhost", 8888)
        Logger.create_logger('c:\\temp\\retrospect.debug.log', "Retrospect Debug",
                             min_log_level=0, dual_logger=lambda x, y=4: __DualLog(x, y))
        UriHandler.CreateUriHandler()
