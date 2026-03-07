# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for DeviceAuthDialog.

``xbmcgui.WindowXMLDialog`` is not provided by the sakee emulator, so this
module injects minimal fakes before importing the dialog under test.
"""

import sys
import threading
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal xbmcgui stubs (injected before importing the dialog module)
# ---------------------------------------------------------------------------

class FakeControl:
    """Records calls made by the dialog on each control."""

    def __init__(self):
        self.label = None
        self.image = None
        self.visible = True
        self.width = None

    def setLabel(self, text):
        self.label = text

    def setImage(self, path):
        self.image = path

    def setVisible(self, flag):
        self.visible = flag

    def setWidth(self, w):
        self.width = w


class FakeWindowXMLDialog:
    """Minimal stand-in for xbmcgui.WindowXMLDialog."""

    def __init__(self, *args, **kwargs):
        self._controls = {}
        self._closed = False

    def getControl(self, control_id):
        if control_id not in self._controls:
            self._controls[control_id] = FakeControl()
        return self._controls[control_id]

    def close(self):
        self._closed = True

    def doModal(self):
        pass


class _FakeListItem:
    """Minimal ListItem stub so sakee's xbmc.py can import from xbmcgui."""
    def __init__(self, *a, **kw):
        pass


# Inject before the module is imported
if "xbmcgui" not in sys.modules:
    _xbmcgui = types.ModuleType("xbmcgui")
    _xbmcgui.WindowXMLDialog = FakeWindowXMLDialog
    _xbmcgui.ListItem = _FakeListItem
    sys.modules["xbmcgui"] = _xbmcgui
else:
    sys.modules["xbmcgui"].WindowXMLDialog = FakeWindowXMLDialog
    if not hasattr(sys.modules["xbmcgui"], "ListItem"):
        sys.modules["xbmcgui"].ListItem = _FakeListItem

# Now it is safe to import the dialog
from resources.lib.deviceauthdialog import (  # noqa: E402
    DeviceAuthDialog,
    ACTION_PREVIOUS_MENU,
    ACTION_NAV_BACK,
    _ID_BTN_CANCEL,
    _ID_BTN_MANUAL,
    _ID_PROGRESS,
    _ID_TIME,
    _ID_QR_IMAGE,
    _ID_QR_TEXT,
    _PROGRESS_BAR_WIDTH,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dialog():
    """Return a DeviceAuthDialog with default content already set."""
    dlg = DeviceAuthDialog("DeviceAuthDialog.xml", "/fake/path")
    dlg.set_content(
        title="Title",
        visit_text="Visit",
        verification_uri="https://example.com/activate",
        enter_code_text="Enter code:",
        user_code="ABC-123",
        expires_in=300,
        cancel_label="Cancel",
    )
    return dlg


def _fake_action(action_id):
    action = MagicMock()
    action.getId.return_value = action_id
    return action


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDeviceAuthDialogInitialState(unittest.TestCase):

    def test_flags_false_after_construction(self):
        dlg = DeviceAuthDialog("DeviceAuthDialog.xml", "/fake/path")
        self.assertFalse(dlg.cancelled)
        self.assertFalse(dlg.manual_login)

    def test_stop_event_not_set_after_construction(self):
        dlg = DeviceAuthDialog("DeviceAuthDialog.xml", "/fake/path")
        self.assertIsInstance(dlg.stop_event, threading.Event)
        self.assertFalse(dlg.stop_event.is_set())


class TestDeviceAuthDialogSetContent(unittest.TestCase):

    def test_fields_stored(self):
        dlg = _make_dialog()
        self.assertEqual(dlg._title, "Title")
        self.assertEqual(dlg._verification_uri, "https://example.com/activate")
        self.assertEqual(dlg._user_code, "ABC-123")
        self.assertEqual(dlg._expires_in, 300)

    def test_qr_path_none_when_no_qr_url(self):
        dlg = _make_dialog()
        self.assertIsNone(dlg._qr_path)
        self.assertIsNone(dlg._qr_url)

    def test_manual_label_none_by_default(self):
        dlg = _make_dialog()
        self.assertIsNone(dlg._manual_label)


class TestUpdateProgress(unittest.TestCase):

    def setUp(self):
        self.dlg = _make_dialog()

    def test_full_bar(self):
        self.dlg.update_progress(100, 300)
        self.assertEqual(self.dlg.getControl(_ID_PROGRESS).width, _PROGRESS_BAR_WIDTH)

    def test_half_bar(self):
        self.dlg.update_progress(50, 150)
        self.assertEqual(self.dlg.getControl(_ID_PROGRESS).width, _PROGRESS_BAR_WIDTH // 2)

    def test_zero_bar(self):
        self.dlg.update_progress(0, 0)
        self.assertEqual(self.dlg.getControl(_ID_PROGRESS).width, 0)

    def test_negative_clamped_to_zero(self):
        self.dlg.update_progress(-10, 0)
        self.assertEqual(self.dlg.getControl(_ID_PROGRESS).width, 0)

    def test_time_format_minutes_and_seconds(self):
        self.dlg.update_progress(100, 90)
        self.assertEqual(self.dlg.getControl(_ID_TIME).label, "1:30")

    def test_time_format_zero(self):
        self.dlg.update_progress(0, 0)
        self.assertEqual(self.dlg.getControl(_ID_TIME).label, "0:00")

    def test_time_format_seconds_only(self):
        self.dlg.update_progress(50, 45)
        self.assertEqual(self.dlg.getControl(_ID_TIME).label, "0:45")

    def test_time_format_leading_zero_on_seconds(self):
        self.dlg.update_progress(100, 65)
        self.assertEqual(self.dlg.getControl(_ID_TIME).label, "1:05")


class TestOnClick(unittest.TestCase):

    def test_cancel_button_sets_cancelled(self):
        dlg = _make_dialog()
        dlg.onClick(_ID_BTN_CANCEL)
        self.assertTrue(dlg.cancelled)
        self.assertFalse(dlg.manual_login)

    def test_cancel_button_calls_close(self):
        dlg = _make_dialog()
        dlg.onClick(_ID_BTN_CANCEL)
        self.assertTrue(dlg._closed)

    def test_manual_button_sets_manual(self):
        dlg = _make_dialog()
        dlg.onClick(_ID_BTN_MANUAL)
        self.assertTrue(dlg.manual_login)
        self.assertFalse(dlg.cancelled)

    def test_manual_button_calls_close(self):
        dlg = _make_dialog()
        dlg.onClick(_ID_BTN_MANUAL)
        self.assertTrue(dlg._closed)

    def test_unknown_control_does_nothing(self):
        dlg = _make_dialog()
        dlg.onClick(9999)
        self.assertFalse(dlg.cancelled)
        self.assertFalse(dlg.manual_login)


class TestOnAction(unittest.TestCase):

    def test_previous_menu_cancels(self):
        dlg = _make_dialog()
        dlg.onAction(_fake_action(ACTION_PREVIOUS_MENU))
        self.assertTrue(dlg.cancelled)

    def test_nav_back_cancels(self):
        dlg = _make_dialog()
        dlg.onAction(_fake_action(ACTION_NAV_BACK))
        self.assertTrue(dlg.cancelled)

    def test_other_action_ignored(self):
        dlg = _make_dialog()
        dlg.onAction(_fake_action(999))
        self.assertFalse(dlg.cancelled)


class TestOnClosed(unittest.TestCase):

    def test_stop_event_is_set(self):
        dlg = _make_dialog()
        dlg.onClosed()
        self.assertTrue(dlg.stop_event.is_set())

    def test_safety_net_sets_cancelled_when_no_explicit_button(self):
        dlg = _make_dialog()
        dlg.onClosed()
        self.assertTrue(dlg.cancelled)

    def test_safety_net_does_not_override_manual(self):
        dlg = _make_dialog()
        dlg._manual = True
        dlg.onClosed()
        self.assertFalse(dlg.cancelled)
        self.assertTrue(dlg.manual_login)

    def test_safety_net_does_not_override_cancelled(self):
        dlg = _make_dialog()
        dlg._cancelled = True
        dlg.onClosed()
        self.assertTrue(dlg.cancelled)


class TestOnInitQrVisibility(unittest.TestCase):

    def _run_onInit(self, dlg):
        """Run onInit with Config and LanguageHelper patched out."""
        with patch("resources.lib.retroconfig.Config") as mock_cfg:
            mock_cfg.rootDir = "/fake"
            with patch("resources.lib.helpers.languagehelper.LanguageHelper"
                       ".get_localized_string", return_value="[mocked]"):
                dlg.onInit()

    def test_no_qr_url_hides_qr_image_and_text(self):
        dlg = _make_dialog()
        self._run_onInit(dlg)
        self.assertFalse(dlg.getControl(_ID_QR_IMAGE).visible)
        self.assertFalse(dlg.getControl(_ID_QR_TEXT).visible)

    def test_qr_url_but_missing_module_hides_image_shows_error(self):
        dlg = _make_dialog()
        with patch("resources.lib.deviceauthdialog.generate_qr_image", return_value=None):
            dlg.set_content(
                title="T", visit_text="V", verification_uri="https://x.com",
                enter_code_text="E", user_code="X", expires_in=60,
                cancel_label="C", qr_url="https://x.com/activate",
            )
        # _qr_path is None (module absent), _qr_url is set
        self.assertIsNone(dlg._qr_path)
        self.assertIsNotNone(dlg._qr_url)
        self._run_onInit(dlg)
        self.assertFalse(dlg.getControl(_ID_QR_IMAGE).visible)
        # The QR text control should have received the missing-addon message
        self.assertIsNotNone(dlg.getControl(_ID_QR_TEXT).label)

    def test_manual_label_none_hides_manual_button(self):
        from resources.lib.deviceauthdialog import _ID_BTN_MANUAL
        dlg = _make_dialog()  # manual_label=None by default
        self._run_onInit(dlg)
        self.assertFalse(dlg.getControl(_ID_BTN_MANUAL).visible)


if __name__ == "__main__":
    unittest.main()
