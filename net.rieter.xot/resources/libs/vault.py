#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import pyaes        #: Pure Python AES
import pyscrypt     #: Pure Python SCrypt
import base64
import random
import string
import hashlib

from logger import Logger
from addonsettings import AddonSettings, LOCAL, KODI
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper


class Vault:
    __Key = None
    __APPLICATION_KEY_SETTING = "application_key"

    def __init__(self):
        # type: (Vault) -> None
        self.__newKeyGeneratedInConstructor = False    # : This was the very first time a key was generated

        # ask for PIN of no key is present
        if Vault.__Key is None:
            key = self.__GetApplicationKey()

            # was there a key? No, let's initialize it.
            if key is None:
                Logger.Warning("No Application Key present. Intializing a new one.")
                key = self.__GetNewKey()
                if not self.ChangePin(key):
                    raise RuntimeError("Error creating Application Key.")
                Logger.Info("Created a new Application Key with MD5: %s (lengt=%s)",
                            hashlib.md5(key).hexdigest(), len(key))
                self.__newKeyGeneratedInConstructor = True

            Vault.__Key = key
            Logger.Trace("Using Application Key with MD5: %s (lengt=%s)", hashlib.md5(key).hexdigest(), len(key))

    def ChangePin(self, applicationKey=None):
        # type: (str) -> bool
        """ Stores an existing ApplicationKey using a new PIN

        @param applicationKey: an existing ApplicationKey that will be stored. If none specified,
                               the existing ApplicationKey of the Vault will be used.
        @return: indication of success
        """

        Logger.Info("Updating the ApplicationKey with a new PIN")

        if self.__newKeyGeneratedInConstructor:
            Logger.Info("A key was just generated, no need to change PINs.")
            return True

        if applicationKey is None:
            Logger.Debug("Using the ApplicationKey from the vault.")
            applicationKey = Vault.__Key
        else:
            Logger.Debug("Using the ApplicationKey from the input parameter.")

        if not applicationKey:
            raise ValueError("No ApplicationKey specified.")

        # Now we get a new PIN and (re)encrypt

        pin = XbmcWrapper.ShowKeyBoard(
            heading=LanguageHelper.GetLocalizedString(LanguageHelper.VaultNewPin),
            hidden=True)
        if not pin:
            XbmcWrapper.ShowNotification(
                "", LanguageHelper.GetLocalizedString(LanguageHelper.VaultNoPin),
                XbmcWrapper.Error)
            return False

        pin2 = XbmcWrapper.ShowKeyBoard(
            heading=LanguageHelper.GetLocalizedString(LanguageHelper.VaultRepeatPin),
            hidden=True)
        if pin != pin2:
            Logger.Critical("Mismatch in PINs")
            XbmcWrapper.ShowNotification(
                "",
                LanguageHelper.GetLocalizedString(LanguageHelper.VaultPinsDontMatch),
                XbmcWrapper.Error)
            return False

        encryptedKey = "%s=%s" % (self.__APPLICATION_KEY_SETTING, applicationKey)

        # let's generate a pin using the scrypt password-based key derivation
        pinKey = self.__GetPBK(pin)
        encryptedKey = self.__Encrypt(encryptedKey, pinKey)
        AddonSettings.SetSetting(Vault.__APPLICATION_KEY_SETTING, encryptedKey, store=LOCAL)
        Logger.Info("Successfully updated the Retrospect PIN")
        return True

    @staticmethod
    def Reset():
        """ Resets the Vault and Retrospect Machine key, making all encrypted values
        useless.

        """

        ok = XbmcWrapper.ShowYesNo(LanguageHelper.GetLocalizedString(LanguageHelper.VaultReset),
                                   LanguageHelper.GetLocalizedString(LanguageHelper.VaultResetConfirm))
        if not ok:
            Logger.Debug("Aborting Reset Vault")
            return

        Logger.Info("Resetting the vault to a new initial state.")
        AddonSettings.SetSetting(Vault.__APPLICATION_KEY_SETTING, "", store=LOCAL)

        # create a vault instance so we initialize a new one with a new PIN.
        Vault()
        return

    def GetChannelSetting(self, channelGuid, settingId):
        # type: (str, str) -> str
        """ Retrieves channel settings for the given channel

        @param channelGuid: The channel object to get the channels for
        @param settingId:   The setting to retrieve
        @rtype : the configured value
        """

        fullSettingId = "channel_%s_%s" % (channelGuid, settingId)
        return self.GetSetting(fullSettingId)

    def GetSetting(self, settingId):
        """ Retrieves an encrypted setting from the Kodi Add-on Settings.

        @param settingId: the ID for the setting to retrieve
        @return:          the decrypted value for the setting
        """

        Logger.Info("Decrypting value for setting '%s'", settingId)
        encryptedValue = AddonSettings.GetSetting(settingId)
        if not encryptedValue:
            return encryptedValue

        try:
            decryptedValue = self.__Decrypt(encryptedValue, Vault.__Key)
            if not decryptedValue.startswith(settingId):
                Logger.Error("Invalid decrypted value for setting '%s'", settingId)
                return None

            decryptedValue = decryptedValue[len(settingId) + 1:]
            Logger.Info("Successfully decrypted value for setting '%s'", settingId)
        except UnicodeDecodeError:
            Logger.Error("Invalid Unicode data returned from decryption. Must be wrong data")
            return None

        return decryptedValue

    def SetSetting(self, settingId, settingName=None, settingActionId=None):
        # type: (str, str, str) -> None
        """ Reads a value for a setting from the keyboard and encryptes it in the Kodi
        Add-on settings

        @param settingId:   the ID for the Kodi Add-on setting to set
        @param settingName: the name to display in the keyboard
        @param settingActionId: the name of the action that was called.

        The setttingActionId defaults to <settingId>_set

        """

        Logger.Info("Encrypting value for setting '%s'", settingId)
        inputValue = XbmcWrapper.ShowKeyBoard(
            "",
            LanguageHelper.GetLocalizedString(LanguageHelper.VaultSpecifySetting) % (settingName or settingId, ))

        if inputValue is None:
            Logger.Debug("Setting of encrypted value cancelled.")
            return

        value = "%s=%s" % (settingId, inputValue)
        encryptedValue = self.__Encrypt(value, Vault.__Key)

        if settingActionId is None:
            settingActionId = "%s_set" % (settingId,)

        Logger.Debug("Updating '%s' and '%s'", settingId, settingActionId)
        AddonSettings.SetSetting(settingId, encryptedValue)
        if inputValue:
            AddonSettings.SetSetting(settingActionId, "******")
        else:
            AddonSettings.SetSetting(settingActionId, "")
        Logger.Info("Successfully encrypted value for setting '%s'", settingId)
        return

    def __GetApplicationKey(self):
        """ Gets the decrypted application key that is used for all the encryption

        @return: the decrypted application key that is used for all the encryption
        """

        applicationKeyEncrypted = AddonSettings.GetSetting(Vault.__APPLICATION_KEY_SETTING, store=LOCAL)
        if not applicationKeyEncrypted:
            applicationKeyEncrypted = AddonSettings.GetSetting(Vault.__APPLICATION_KEY_SETTING, store=KODI)
            if not applicationKeyEncrypted:
                return None

            Logger.Info("Moved ApplicationKey to local storage")
            AddonSettings.SetSetting(Vault.__APPLICATION_KEY_SETTING, applicationKeyEncrypted, store=LOCAL)

        vaultIncorrectPin = LanguageHelper.GetLocalizedString(LanguageHelper.VaultIncorrectPin)
        pin = XbmcWrapper.ShowKeyBoard(
            heading=LanguageHelper.GetLocalizedString(LanguageHelper.VaultInputPin),
            hidden=True)
        if not pin:
            XbmcWrapper.ShowNotification("", vaultIncorrectPin, XbmcWrapper.Error)
            raise RuntimeError("Incorrect Retrospect PIN specified")
        pinKey = self.__GetPBK(pin)
        applicationKey = self.__Decrypt(applicationKeyEncrypted, pinKey)
        if not applicationKey.startswith(Vault.__APPLICATION_KEY_SETTING):
            Logger.Critical("Invalid Retrospect PIN")
            XbmcWrapper.ShowNotification("", vaultIncorrectPin, XbmcWrapper.Error)
            raise RuntimeError("Incorrect Retrospect PIN specified")

        applicationKeyValue = applicationKey[len(Vault.__APPLICATION_KEY_SETTING) + 1:]
        Logger.Info("Successfully decrypted the ApplicationKey.")
        return applicationKeyValue

    def __Encrypt(self, data, key):
        # type: (str, str) -> str
        """ Encrypt data based on a given passPhrase

        @param data: [string] the data to encrypt
        """

        Logger.Debug("Encrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)
        return base64.b64encode(aes.encrypt(data))

    def __Decrypt(self, data, key):
        # type: (str, str) -> str
        """ Retrieves a password from the keyring. If none is found, None is return.

        @param data: [string] the data to decrypt
        @param key:  [string] the key to use for decrypting
        @return:     [string] the password retrieved from the keyring
        """

        Logger.Debug("Decrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)
        return aes.decrypt(base64.b64decode(data))

    def __GetNewKey(self, length=32):
        # type: (int) -> str
        """ Returns a random key

        @param length: the lenght of the key
        @return: a random key of the given length
        """
        return ''.join(random.choice(string.digits + string.letters + string.punctuation)
                       for _ in range(length))

    def __GetPBK(self, pin):
        salt = AddonSettings.GetClientId()
        pbk = pyscrypt.hash(password=pin,
                            salt=salt,
                            N=2 ** 7,  # should be so that Raspberry Pi can handle it
                            # N=1024,
                            r=1,
                            p=1,
                            dkLen=32)
        Logger.Trace("Generated PBK with MD5: %s", hashlib.md5(pbk).hexdigest())
        return pbk
