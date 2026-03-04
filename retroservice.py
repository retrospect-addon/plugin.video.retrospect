# SPDX-License-Identifier: GPL-3.0-or-later

import glob as _glob
import os
import re
import shutil
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcvfs

_ADDON = xbmcaddon.Addon()
_ADDON_DATA = xbmcvfs.translatePath(_ADDON.getAddonInfo("profile"))
_ADDON_PATH = xbmcvfs.translatePath(_ADDON.getAddonInfo("path"))
_EPG_SIGNAL_FILE = os.path.join(_ADDON_DATA, "nlziet_epg_signal_at")
_EPG_PROGLOC_KEY = "nlziet_epg_progloc_cache"
_PVR_GENRES_VERSION = 2


def _log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[RetroService] " + msg, level)


_log("addon_data=%s signal_file=%s" % (_ADDON_DATA, _EPG_SIGNAL_FILE), xbmc.LOGINFO)


def autorun_retrospect():
    if _ADDON.getSetting("auto_run") == "true":
        xbmc.executebuiltin("RunAddon(plugin.video.retrospect)")


def _merge_genre_xmls():
    """Merge base pvr_genres.xml with any per-channel genres.xml overrides.

    Channels place a ``genres.xml`` alongside their channel module
    (e.g. ``channels/channel.nlziet/nlziet/genres.xml``).  Entries in
    channel files override same-genreId entries from the base file.

    :return: Merged XML string, or None on error.
    :rtype: str|None
    """
    base = os.path.join(_ADDON_PATH, "resources", "data", "pvr_genres.xml")
    if not os.path.isfile(base):
        _log("pvr_genres.xml not found at %s" % base, xbmc.LOGWARNING)
        return None

    try:
        base_root = ET.parse(base).getroot()
    except ET.ParseError as e:
        _log("Failed to parse pvr_genres.xml: %s" % e, xbmc.LOGWARNING)
        return None

    # Ordered: genreId -> display text.  Base first; channels override.
    genres = {}
    for elem in base_root.findall("genre"):
        gid = elem.get("genreId")
        if gid and elem.text:
            genres[gid] = elem.text.strip()

    # Discover per-channel genres.xml files and merge
    channels_dir = os.path.join(_ADDON_PATH, "channels")
    if os.path.isdir(channels_dir):
        for dirpath, _dirs, files in os.walk(channels_dir):
            if "genres.xml" not in files:
                continue
            path = os.path.join(dirpath, "genres.xml")
            try:
                croot = ET.parse(path).getroot()
                count = 0
                for elem in croot.findall("genre"):
                    gid = elem.get("genreId")
                    if gid and elem.text:
                        genres[gid] = elem.text.strip()
                        count += 1
                _log("Merged %d genre entries from %s" % (count, path))
            except ET.ParseError as e:
                _log("Skipping %s (parse error: %s)" % (path, e), xbmc.LOGWARNING)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!--',
        '  Retrospect merged genre-text mappings for pvr.iptvsimple.',
        '  Generated from base pvr_genres.xml + per-channel genres.xml overrides.',
        '  version: %d' % _PVR_GENRES_VERSION,
        '-->',
        '',
        '<genres>',
        '  <name>Retrospect Genre Mappings</name>',
        '',
    ]
    for gid, text in genres.items():
        lines.append('  <genre genreId="%s">%s</genre>' % (gid, text))
    lines += ['</genres>', '']
    return '\n'.join(lines)


def _set_xml_setting(content, setting_id, value):
    """Update or append a ``<setting id="...">`` element in raw XML text.

    Strips the ``default="true"`` attribute (marks a user-configured value)
    and replaces the element text.  Inserts a new element before
    ``</settings>`` if the id is absent.

    :param str content: Raw XML file content.
    :param str setting_id: The ``id`` attribute to match.
    :param str value: The new element text.
    :return: Updated XML content.
    :rtype: str
    """
    pattern = r'<setting id="%s"[^>]*>[^<]*</setting>' % re.escape(setting_id)
    replacement = '<setting id="%s">%s</setting>' % (setting_id, value)
    if re.search(pattern, content):
        return re.sub(pattern, replacement, content)
    # Not present — insert before closing tag
    new_line = '    <setting id="%s">%s</setting>\n' % (setting_id, value)
    return content.replace("</settings>", new_line + "</settings>")


def _configure_pvr_instances(pvr_data):
    """Enable genre-text mapping in pvr.iptvsimple instances that use our playlist.

    Scans all ``instance-settings-N.xml`` files in *pvr_data*.  For each
    instance whose ``m3uPath`` contains ``service.iptv.manager`` (i.e. it
    was set up by IPTV Manager for Retrospect), set:

    - ``useEpgGenreText`` → ``true``
    - ``genresPathType``  → ``0``  (local file)
    - ``genresPath``      → the installed genres.xml path

    :param str pvr_data: pvr.iptvsimple profile directory.
    """
    genres_path = (
        "special://userdata/addon_data/pvr.iptvsimple"
        "/genres/genreTextMappings/genres.xml"
    )

    for instance_file in _glob.glob(os.path.join(pvr_data, "instance-settings-*.xml")):
        try:
            with open(instance_file, encoding="utf-8") as fh:
                content = fh.read()
        except OSError as e:
            _log("Failed to read %s: %s" % (instance_file, e), xbmc.LOGWARNING)
            continue

        if "service.iptv.manager" not in content:
            continue

        original = content
        content = _set_xml_setting(content, "useEpgGenreText", "true")
        content = _set_xml_setting(content, "genresPathType", "0")
        content = _set_xml_setting(content, "genresPath", genres_path)

        if content != original:
            try:
                with open(instance_file, "w", encoding="utf-8") as fh:
                    fh.write(content)
                _log("Updated genre settings in %s" % instance_file, xbmc.LOGINFO)
            except OSError as e:
                _log("Failed to write %s: %s" % (instance_file, e), xbmc.LOGWARNING)


def _setup_pvr_genres():
    """Install merged genre-text mapping for pvr.iptvsimple if needed.

    Merges the base ``resources/data/pvr_genres.xml`` with any per-channel
    ``genres.xml`` files found under ``channels/**/``.  Channel-provided
    entries override same-genreId entries from the base file, so each
    channel controls only the genres it actually emits.

    Also enables ``useEpgGenreText`` in any pvr.iptvsimple instance that
    uses the service.iptv.manager playlist.
    """
    try:
        pvr_addon = xbmcaddon.Addon("pvr.iptvsimple")
    except RuntimeError:
        _log("pvr.iptvsimple not installed — skipping genre setup")
        return

    pvr_data = xbmcvfs.translatePath(pvr_addon.getAddonInfo("profile"))
    target_dir = os.path.join(pvr_data, "genres", "genreTextMappings")
    target_file = os.path.join(target_dir, "genres.xml")

    version_marker = "version: %d" % _PVR_GENRES_VERSION
    if os.path.isfile(target_file):
        try:
            with open(target_file) as fh:
                head = fh.read(512)
            if version_marker in head:
                _log("pvr_genres v%d already installed" % _PVR_GENRES_VERSION)
                _configure_pvr_instances(pvr_data)
                return
        except OSError:
            pass

    merged = _merge_genre_xmls()
    if not merged:
        return

    os.makedirs(target_dir, exist_ok=True)
    try:
        with open(target_file, "w", encoding="utf-8") as fh:
            fh.write(merged)
        _log("Installed pvr_genres v%d -> %s" % (_PVR_GENRES_VERSION, target_file),
             xbmc.LOGINFO)
    except OSError as e:
        _log("Failed to write %s: %s" % (target_file, e), xbmc.LOGWARNING)
        return

    _configure_pvr_instances(pvr_data)


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
        _setup_pvr_genres()
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

