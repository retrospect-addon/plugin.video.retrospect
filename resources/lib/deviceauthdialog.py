# SPDX-License-Identifier: GPL-3.0-or-later
"""Device flow authentication dialog backed by a Kodi XML skin."""

import os
import threading

import xbmcgui

from resources.lib.logger import Logger

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

# IDs match the visual top-to-bottom order in DeviceAuthDialog.xml (×10 spacing).
_ID_TITLE = 10
_ID_LOGO = 20
_ID_QR_TEXT = 30
_ID_QR_IMAGE = 40
_ID_ALWAYS_TEXT = 50
_ID_URI = 60
_ID_CODE_TEXT = 70
_ID_CODE = 80
_ID_TIME = 90
_ID_PROGRESS = 100
_ID_BTN_CANCEL = 110
_ID_BTN_MANUAL = 120

_PROGRESS_BAR_WIDTH = 1000  # must match DeviceAuthDialog.xml blue fill image width


def generate_qr_image(url):
    """Generate a QR code PNG and return the file path.

    Requires the ``script.module.qrcode`` Kodi addon to be installed.
    Returns ``None`` gracefully when the addon is absent or generation fails.

    :param str url:  URL to encode.
    :return:         Absolute path to the generated PNG, or None on failure.
    :rtype:          str | None
    """

    from resources.lib.retroconfig import Config
    cache_dir = Config.cacheDir
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "qr.png")
    try:
        import qrcode
        img = qrcode.make(url)
        img.save(path)
        return path
    except Exception:
        Logger.error("Failed to generate QR code", exc_info=True)
        return None


class DeviceAuthDialog(xbmcgui.WindowXMLDialog):
    """Device flow dialog: URL, user code, countdown, optional manual-login button.

    All user-visible text is supplied via constructor parameters so callers
    can pass localized strings.  The dialog reports which button was pressed
    via the ``cancelled`` and ``manual_login`` properties.
    """

    def __init__(self, *args, **kwargs):
        """Create the dialog.

        Pass ``("DeviceAuthDialog.xml", addon_path)`` as positional arguments;
        all dialog content is supplied later via :meth:`set_content`.
        """

        super().__init__(*args, **kwargs)
        self._title = ""
        self._visit_text = ""
        self._verification_uri = ""
        self._enter_code_text = ""
        self._user_code = ""
        self._expires_in = 0
        self._cancel_label = ""
        self._manual_label = None
        self._qr_url = None
        self._qr_path = None
        self._logo_path = None
        self._cancelled = False
        self._manual = False
        self._stop_event = threading.Event()

    def set_content(self, title, visit_text, verification_uri,
                    enter_code_text, user_code, expires_in, cancel_label,
                    manual_label=None, qr_url=None, logo_path=None):
        """Set all dialog content before calling ``show()``.

        :param str title:             Dialog title.
        :param str visit_text:        Instruction text above the URL.
        :param str verification_uri:  URL to display.
        :param str enter_code_text:   Text above the user code.
        :param str user_code:         The code to display.
        :param int expires_in:        Seconds until the code expires.
        :param str cancel_label:      Label for the cancel button.
        :param str|None manual_label: Label for the manual-login button (omit to hide).
        :param str|None qr_url:       URL to encode as a QR code (omit for text-only).
        :param str|None logo_path:    Path to a logo image for the header (defaults to
                                      the Retrospect addon icon when omitted).
        """

        self._title = title
        self._visit_text = visit_text
        self._verification_uri = verification_uri
        self._enter_code_text = enter_code_text
        self._user_code = user_code
        self._expires_in = expires_in
        self._cancel_label = cancel_label
        self._manual_label = manual_label
        self._qr_url = qr_url
        self._qr_path = generate_qr_image(qr_url) if qr_url else None
        self._logo_path = logo_path

    # -- Kodi lifecycle ----------------------------------------------------

    def onInit(self):
        self.getControl(_ID_TITLE).setLabel(self._title)
        self.getControl(_ID_ALWAYS_TEXT).setLabel(self._visit_text)
        self.getControl(_ID_URI).setLabel(self._verification_uri)
        self.getControl(_ID_CODE_TEXT).setLabel(self._enter_code_text)
        self.getControl(_ID_CODE).setLabel(self._user_code)
        self.getControl(_ID_BTN_CANCEL).setLabel(self._cancel_label)
        btn_manual = self.getControl(_ID_BTN_MANUAL)
        if self._manual_label is None:
            btn_manual.setVisible(False)
        else:
            btn_manual.setLabel(self._manual_label)
        if self._qr_path:
            from resources.lib.helpers.languagehelper import LanguageHelper
            qr_ctrl = self.getControl(_ID_QR_IMAGE)
            qr_ctrl.setImage(self._qr_path)
            qr_ctrl.setVisible(True)
            self.getControl(_ID_QR_TEXT).setLabel(
                LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupQrInstruction))
        elif self._qr_url:
            from resources.lib.helpers.languagehelper import LanguageHelper
            self.getControl(_ID_QR_IMAGE).setVisible(False)
            self.getControl(_ID_QR_TEXT).setLabel(
                LanguageHelper.get_localized_string(LanguageHelper.QrAddonMissing))
        else:
            self.getControl(_ID_QR_IMAGE).setVisible(False)
            self.getControl(_ID_QR_TEXT).setVisible(False)
        from resources.lib.retroconfig import Config
        logo_path = self._logo_path or os.path.join(
            Config.rootDir, "resources", "media", "icon.png")
        self.getControl(_ID_LOGO).setImage(logo_path)
        self.update_progress(100, self._expires_in)

    # -- Public interface --------------------------------------------------

    @property
    def cancelled(self):
        return self._cancelled

    @property
    def manual_login(self):
        return self._manual

    @property
    def stop_event(self) -> threading.Event:
        """Event set when the dialog closes for any reason.

        Background threads can block on ``stop_event.wait(timeout)`` instead of
        busy-polling ``cancelled``/``manual_login``.  The event is set inside
        ``onClosed()`` before any other cleanup, so it fires for every close
        path: button click, Escape/Back, programmatic ``close()``, Kodi shutdown.
        """
        return self._stop_event

    def update_progress(self, percent, remaining_seconds):
        """Update the progress bar and time remaining label."""

        bar_width = max(0, int(_PROGRESS_BAR_WIDTH * percent / 100))
        self.getControl(_ID_PROGRESS).setWidth(bar_width)
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        self.getControl(_ID_TIME).setLabel("{:d}:{:02d}".format(mins, secs))

    # -- Kodi event handlers -----------------------------------------------

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._cancelled = True
            self.close()

    def onClick(self, controlId):
        if controlId == _ID_BTN_CANCEL:
            self._cancelled = True
            self.close()
        elif controlId == _ID_BTN_MANUAL:
            self._manual = True
            self.close()

    def onClosed(self):
        # Signal background workers immediately, regardless of close reason.
        self._stop_event.set()
        # Safety net: if the dialog was closed without an explicit button press
        # (e.g. a remote Back that bypassed onAction), treat it as a cancellation.
        if not self._cancelled and not self._manual:
            self._cancelled = True
