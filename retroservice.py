# SPDX-License-Identifier: GPL-3.0-or-later

import os
import time

import xbmc
import xbmcaddon
import xbmcvfs

_ADDON = xbmcaddon.Addon()
_ADDON_DATA = xbmcvfs.translatePath(_ADDON.getAddonInfo("profile"))
_EPG_SIGNAL_FILE = os.path.join(_ADDON_DATA, "nlziet_epg_signal_at")
_EPG_PROGLOC_KEY = "nlziet_epg_progloc_cache"


def autorun_retrospect():
    if _ADDON.getSetting("auto_run") == "true":
        xbmc.executebuiltin("RunAddon(plugin.video.retrospect)")


def _iptv_manager_signal():
    """Set last_refreshed = "0" in IPTV Manager so it calls create_iptv_epg again."""
    try:
        xbmcaddon.Addon("service.iptv.manager").setSetting("last_refreshed", "0")
    except Exception:
        pass


def _has_epg_data():
    """Return True if the NLZIET progloc cache has ever been written."""
    settings_path = os.path.join(_ADDON_DATA, "settings.json")
    try:
        with open(settings_path) as fh:
            return _EPG_PROGLOC_KEY in fh.read()
    except OSError:
        return False


def _check_epg_signal():
    """If the signal file has matured, fire an IPTV Manager refresh and remove it."""
    if not os.path.isfile(_EPG_SIGNAL_FILE):
        return
    try:
        with open(_EPG_SIGNAL_FILE) as fh:
            signal_at = float(fh.read().strip())
    except (OSError, ValueError):
        return
    if time.time() < signal_at:
        return
    _iptv_manager_signal()
    try:
        os.remove(_EPG_SIGNAL_FILE)
    except OSError:
        pass


class RetroService(xbmc.Monitor):
    """Background service: auto-run + NLZIET EPG signal relay."""

    def __init__(self):
        super(RetroService, self).__init__()
        self._initial_signal_sent = False

    def run(self):
        autorun_retrospect()
        self._tick()  # run once immediately; don't wait 30s for the first check
        while not self.waitForAbort(30):
            self._tick()

    def _tick(self):
        # Relay any signal written by create_iptv_epg
        _check_epg_signal()
        # On first ticks: trigger initial EPG fetch if no data yet
        if not self._initial_signal_sent and not _has_epg_data():
            if not os.path.isfile(_EPG_SIGNAL_FILE):
                try:
                    with open(_EPG_SIGNAL_FILE, "w") as fh:
                        fh.write(str(time.time() + 5))
                except OSError:
                    pass
            self._initial_signal_sent = True


RetroService().run()

