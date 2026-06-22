# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch, call

from resources.lib.vault import Vault


def _reset_vault_key():
    Vault._Vault__Key = None


class TestVaultGetWithoutKey(unittest.TestCase):
    """get_* returns None silently when the vault has never been initialised."""

    def setUp(self):
        _reset_vault_key()

    def tearDown(self):
        _reset_vault_key()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_get_setting_returns_none_without_vault(self, mock_xbmc, mock_settings):
        """SUCCESS → None returned, no PIN or howto dialog shown."""

        mock_settings.get_setting.return_value = None

        v = Vault()
        result = v.get_setting("some_setting")

        self.assertIsNone(result)
        mock_xbmc.show_key_board.assert_not_called()
        mock_xbmc.show_text.assert_not_called()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_get_channel_setting_returns_none_without_vault(self, mock_xbmc, mock_settings):
        """SUCCESS → None returned, no PIN or howto dialog shown."""

        mock_settings.get_setting.return_value = None

        v = Vault()
        result = v.get_channel_setting("guid-123", "my_setting")

        self.assertIsNone(result)
        mock_xbmc.show_key_board.assert_not_called()
        mock_xbmc.show_text.assert_not_called()


class TestVaultInit(unittest.TestCase):
    """Vault.__init__ is silent when no key is stored — no prompts of any kind."""

    def setUp(self):
        _reset_vault_key()

    def tearDown(self):
        _reset_vault_key()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_init_does_not_prompt_when_no_key_stored(self, mock_xbmc, mock_settings):
        """SUCCESS → constructor emits no dialogs when the vault has never been set up."""

        mock_settings.get_setting.return_value = None

        Vault()

        mock_xbmc.show_key_board.assert_not_called()
        mock_xbmc.show_text.assert_not_called()
        mock_xbmc.show_dialog.assert_not_called()
        self.assertIsNone(Vault._Vault__Key)


class TestVaultSetTriggersInit(unittest.TestCase):
    """set_* triggers PIN setup when vault is not yet initialised."""

    def setUp(self):
        _reset_vault_key()

    def tearDown(self):
        _reset_vault_key()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_set_setting_triggers_howto_and_pin_when_no_vault(self, mock_xbmc, mock_settings):
        """SUCCESS → howto shown and PIN dialogs fired before storing the value."""

        mock_settings.get_setting.return_value = None
        mock_settings.get_client_id.return_value = "test-client-id"
        mock_xbmc.show_key_board.side_effect = ["mypin", "mypin", "mysecret"]

        v = Vault()
        v.set_setting("my_setting", setting_name="My Password")

        mock_xbmc.show_text.assert_called_once()
        self.assertGreaterEqual(mock_xbmc.show_key_board.call_count, 2)

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_set_setting_does_not_trigger_init_when_vault_already_set(
            self, mock_xbmc, mock_settings):
        """SUCCESS → no howto shown when vault key already cached."""

        Vault._Vault__Key = b"a" * 32
        mock_xbmc.show_key_board.return_value = "mysecret"

        v = Vault()
        v.set_setting("my_setting", setting_name="My Password")

        mock_xbmc.show_text.assert_not_called()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_set_channel_setting_triggers_howto_and_pin_when_no_vault(
            self, mock_xbmc, mock_settings):
        """SUCCESS → howto and PIN setup triggered via set_channel_setting when no key exists."""

        mock_settings.get_setting.return_value = None
        mock_settings.get_client_id.return_value = "test-client-id"
        mock_xbmc.show_key_board.side_effect = ["mypin", "mypin", "mysecret"]

        v = Vault()
        v.set_channel_setting("guid-abc", "password", setting_name="Channel Password")

        mock_xbmc.show_text.assert_called_once()
        self.assertGreaterEqual(mock_xbmc.show_key_board.call_count, 2)

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_set_setting_does_not_encrypt_when_pin_setup_cancelled(self, mock_xbmc, mock_settings):
        """SUCCESS → nothing stored when user cancels PIN creation during vault init."""

        mock_settings.get_setting.return_value = None
        mock_xbmc.show_key_board.return_value = None

        v = Vault()
        v.set_setting("my_setting", setting_name="My Password")

        mock_settings.set_setting.assert_not_called()


class TestVaultGetAfterInit(unittest.TestCase):
    """get_setting decrypts normally once the vault key is cached."""

    def setUp(self):
        _reset_vault_key()

    def tearDown(self):
        _reset_vault_key()

    @patch("resources.lib.vault.AddonSettings")
    def test_get_setting_returns_none_for_unset_encrypted_value(self, mock_settings):
        """SUCCESS → None returned when no encrypted value is stored for the key."""

        Vault._Vault__Key = b"a" * 32
        mock_settings.get_setting.return_value = None

        v = Vault()
        result = v.get_setting("some_setting")

        self.assertIsNone(result)


class TestVaultReset(unittest.TestCase):
    """reset() clears the cached key and immediately prompts for a new PIN."""

    def setUp(self):
        _reset_vault_key()

    def tearDown(self):
        _reset_vault_key()

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_reset_confirmed_clears_key_and_triggers_pin_setup(self, mock_xbmc, mock_settings):
        """SUCCESS → key cleared, howto shown, PIN creation dialogs fired."""

        Vault._Vault__Key = b"a" * 32
        mock_settings.get_setting.return_value = None
        mock_settings.get_client_id.return_value = "test-client-id"
        mock_xbmc.show_yes_no.return_value = True
        mock_xbmc.show_key_board.side_effect = ["newpin", "newpin"]

        Vault.reset()

        mock_xbmc.show_text.assert_called_once()
        self.assertGreaterEqual(mock_xbmc.show_key_board.call_count, 2)

    @patch("resources.lib.vault.AddonSettings")
    @patch("resources.lib.vault.XbmcWrapper")
    def test_reset_cancelled_preserves_existing_key(self, mock_xbmc, mock_settings):
        """SUCCESS → no changes when user cancels the reset confirmation."""

        Vault._Vault__Key = b"a" * 32
        mock_xbmc.show_yes_no.return_value = False

        Vault.reset()

        mock_xbmc.show_text.assert_not_called()
        self.assertIsNotNone(Vault._Vault__Key)
