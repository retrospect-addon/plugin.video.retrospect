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


def _log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[RetroService] " + msg, level)


_log("addon_data=%s signal_file=%s" % (_ADDON_DATA, _EPG_SIGNAL_FILE), xbmc.LOGINFO)


def autorun_retrospect():
    if _ADDON.getSetting("auto_run") == "true":
        xbmc.executebuiltin("RunAddon(plugin.video.retrospect)")


def _iptv_manager_signal():
    """Set last_refreshed = "0" in IPTV Manager so it calls create_iptv_epg again."""
    try:
        xbmcaddon.Addon("service.iptv.manager").setSetting("last_refreshed", "0")
        _log("IPTV Manager last_refreshed reset", xbmc.LOGINFO)
    except Exception as e:
        _log("IPTV Manager signal failed: %s" % e, xbmc.LOGWARNING)


def _has_epg_data():
    """Return True if the NLZIET progloc cache has ever been written."""
    settings_path = os.path.join(_ADDON_DATA, "settings.json")
    try:
        with open(settings_path) as fh:
            result = _EPG_PROGLOC_KEY in fh.read()
    except OSError:
        result = False
    _log("has_epg_data=%s (path=%s)" % (result, settings_path))
    return result


def _check_epg_signal():
    """If the signal file has matured, fire an IPTV Manager refresh and remove it."""
    if not os.path.isfile(_EPG_SIGNAL_FILE):
        _log("no signal file")
        return
    try:
        with open(_EPG_SIGNAL_FILE) as fh:
            signal_at = float(fh.read().strip())
    except (OSError, ValueError):
        return
    now = time.time()
    remaining = signal_at - now
    if remaining > 0:
        _log("signal_at=%.1f now=%.1f (%.1fs remaining)" % (signal_at, now, remaining))
        return
    _log("signal matured — triggering IPTV Manager", xbmc.LOGINFO)
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
        self._tick_count = 0

    def run(self):
        _log("started", xbmc.LOGINFO)
        autorun_retrospect()
        self._tick()  # run once immediately; don't wait 30s for the first check
        while not self.waitForAbort(30):
            self._tick()

    def _tick(self):
        self._tick_count += 1
        _log("tick #%d" % self._tick_count)
        # Relay any signal written by create_iptv_epg
        _check_epg_signal()
        # On first tick: trigger initial EPG fetch if no data yet
        if not self._initial_signal_sent and not _has_epg_data():
            if not os.path.isfile(_EPG_SIGNAL_FILE):
                try:
                    with open(_EPG_SIGNAL_FILE, "w") as fh:
                        fh.write(str(time.time() + 5))
                    _log("no EPG data yet — wrote initial trigger to %s" % _EPG_SIGNAL_FILE,
                         xbmc.LOGINFO)
                except OSError as e:
                    _log("failed to write initial trigger: %s" % e, xbmc.LOGWARNING)
            self._initial_signal_sent = True


RetroService().run()

