# SPDX-License-Identifier: GPL-3.0-or-later
"""Channel sort-order dialog backed by a Kodi XML skin."""

import xbmcgui

from resources.lib.logger import Logger

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

# Control IDs — must match ChannelOrderDialog.xml
_ID_TITLE = 10
_ID_LIST = 100
_ID_BTN_UP = 200
_ID_BTN_DOWN = 210
_ID_BTN_OK = 300
_ID_BTN_CANCEL = 310


class ChannelOrderDialog(xbmcgui.WindowXMLDialog):
    """Dialog that lets the user drag channels up/down to set a custom order.

    Usage::

        dialog = ChannelOrderDialog("ChannelOrderDialog.xml", addon_path)
        dialog.set_channels(channels)  # list[ChannelInfo]
        dialog.show()
        if not dialog.cancelled:
            ordered_guids = dialog.result_guids  # list[str]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._channels = []      # list[ChannelInfo] in display order
        self._cancelled = True

    def set_channels(self, channels):
        """Populate the dialog with the initial channel order.

        :param list channels: list of ChannelInfo objects in default order.
        """
        self._channels = list(channels)

    @property
    def cancelled(self):
        """True if the user dismissed without saving."""
        return self._cancelled

    @property
    def result_guids(self):
        """Ordered list of channel GUIDs reflecting the user's chosen order."""
        return [c.guid for c in self._channels]

    # -- Kodi lifecycle --------------------------------------------------------

    def onInit(self):
        Logger.debug("ChannelOrderDialog::onInit")
        title_ctrl = self.getControl(_ID_TITLE)
        title_ctrl.setLabel(self._get_title())

        ok_btn = self.getControl(_ID_BTN_OK)
        ok_btn.setLabel(self._get_ok_label())

        cancel_btn = self.getControl(_ID_BTN_CANCEL)
        cancel_btn.setLabel(self._get_cancel_label())

        self._refresh_list()

    def onClose(self):
        Logger.debug("ChannelOrderDialog::onClose (cancelled=%s)", self._cancelled)

    def onClick(self, control_id):
        if control_id == _ID_BTN_OK:
            self._cancelled = False
            self.close()
        elif control_id == _ID_BTN_CANCEL:
            self._cancelled = True
            self.close()
        elif control_id == _ID_BTN_UP:
            self._move_selected(-1)
        elif control_id == _ID_BTN_DOWN:
            self._move_selected(1)

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._cancelled = True
            self.close()

    # -- Private helpers -------------------------------------------------------

    def _get_title(self):
        from resources.lib.helpers.languagehelper import LanguageHelper
        return LanguageHelper.get_localized_string(LanguageHelper.SortChannels)

    def _get_ok_label(self):
        import xbmc
        return xbmc.getLocalizedString(186)  # Kodi built-in: "OK"

    def _get_cancel_label(self):
        import xbmc
        return xbmc.getLocalizedString(222)  # Kodi built-in: "Cancel"

    def _refresh_list(self):
        """Rebuild the list control from self._channels."""
        list_ctrl = self.getControl(_ID_LIST)
        list_ctrl.reset()
        items = []
        for channel in self._channels:
            item = xbmcgui.ListItem(label=channel.channelName)
            item.setArt({"icon": channel.icon or "", "thumb": channel.icon or ""})
            items.append(item)
        list_ctrl.addItems(items)

    def _move_selected(self, direction):
        """Move the focused list item up (-1) or down (+1) by one position."""
        list_ctrl = self.getControl(_ID_LIST)
        pos = list_ctrl.getSelectedPosition()
        new_pos = pos + direction
        if new_pos < 0 or new_pos >= len(self._channels):
            return
        self._channels[pos], self._channels[new_pos] = \
            self._channels[new_pos], self._channels[pos]
        self._refresh_list()
        list_ctrl.selectItem(new_pos)
