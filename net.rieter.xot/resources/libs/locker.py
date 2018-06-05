# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA. 
# ===============================================================================
import sys

import xbmc


class LockWithDialog(object):
    """ Decorator Class that locks a method using a busy dialog """

    BusyDialog = "busydialognocancel" if int(xbmc.getInfoLabel("system.buildversion").split(".")[0]) >= 18 else "busydialog"

    @staticmethod
    def CloseBusyDialog():
        xbmc.executebuiltin("Dialog.Close({0})".format(LockWithDialog.BusyDialog))
        return

    def __init__(self, logger=None):
        """ Initializes the decorator with a specific method.

        We need to use the Decorator as a function @LockWithDialog() to get the
        'self' parameter passed on.

        """

        self.logger = logger
        return

    def __call__(self, wrappedFunction):
        """ When the method is called this is executed. """

        def __InnerWrappedFunction(*args, **kwargs):
            """ Function that get's called instead of the decorated function """

            # show the busy dialog
            if self.logger:
                self.logger.Debug("Locking interface and showing '%s'", LockWithDialog.BusyDialog)

            xbmc.executebuiltin("ActivateWindow({0})".format(LockWithDialog.BusyDialog))
            try:
                response = wrappedFunction(*args, **kwargs)
                # time.sleep(2)
            except Exception:
                # re-raise the exception with the original traceback info
                # see http://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
                errorInfo = sys.exc_info()
                raise errorInfo[1], None, errorInfo[2]

            finally:
                # Hide the busy Dialog
                LockWithDialog.CloseBusyDialog()
                if self.logger:
                    self.logger.Debug("Un-locking interface and hiding '%s'",
                                      LockWithDialog.BusyDialog)
            return response

        return __InnerWrappedFunction
