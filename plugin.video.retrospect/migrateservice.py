import os
import io
import json
import xbmc
import xbmcgui

# Initialize all the paths correctly
from initializer import Initializer  # nopep8
Initializer.set_unicode()
currentPath = Initializer.setup_python_paths()

from retroconfig import Config


def migrate_profile(new_profile, add_on_id, kodi_add_on_dir, add_on_name):
    """ Migrates the old user profile.

    :param str|unicode new_profile:     The new profile folder.
    :param str|unicode add_on_id:       The new add-on id.
    :param str|unicode kodi_add_on_dir: The Kodi add-on dir.
    :param str|unicode add_on_name:     The name of the current add-on.

    """

    old_add_on_id = "net.rieter.xot"
    log_level = xbmc.LOGNOTICE

    xbmc.log("Retrospect: Checking if migration of profile is required", xbmc.LOGDEBUG)
    # If the profile already existed, just stop here.
    if os.path.isdir(new_profile):
        xbmc.log("Retrospect: Profile already migrated", log_level)
        return

    import shutil
    d = xbmcgui.Dialog()

    # If an old add-on with the old ID was found, disable and rename it.
    old_add_on_path = os.path.abspath(os.path.join(kodi_add_on_dir, "..", old_add_on_id))
    if os.path.isdir(old_add_on_path):
        xbmc.log("Retrospect: Disabling add-on from {}".format(old_add_on_path), log_level)

        # Disable it.
        data = {
            "jsonrpc": "2.0",
            "method": "Addons.SetAddonEnabled",
            "params": {
                "addonid": old_add_on_id,
                "enabled": False},
            "id": 1
        }
        result = xbmc.executeJSONRPC(json.dumps(data))
        xbmc.log(result, log_level)
        result = json.loads(result)
        if not result or "error" in result:
            xbmc.log("Retrospect: Error disabling {}".format(old_add_on_id), xbmc.LOGERROR)

        # Rename it.
        old_add_on_xml = os.path.join(old_add_on_path, "addon.xml")
        if os.path.exists(old_add_on_xml):
            with io.open(old_add_on_xml, mode="r", encoding='utf-8') as fp:
                content = fp.read()

            if "<broken>" not in content:
                xbmc.log("Retrospect: Marking add-on {} as broken".format(old_add_on_path), log_level)
                content = content.replace(
                    '</language>',
                    '</language>\n        '
                    '<broken>New Add-on is used. Please install version 4.8 or higher.</broken>')
                with io.open(old_add_on_xml, mode='w+', encoding='utf-8') as fp:
                    fp.write(content)
            d.ok("Retrospect", "Retrospect changed add-on ID. The user data will now be migrated, "
                               "so no data will be lost. After the migration has completed, "
                               "restart Kodi to complete the change. After the restart update "
                               "any shortcut you had to Retrospect. The Retrospect marked as <broken> "
                               "can be uninstalled.")

        xbmc.log("Retrospect: Reloading all Kodi Add-ons information", log_level)
        xbmc.executebuiltin("UpdateLocalAddons")

    # If there was an old profile, migrate it.
    old_profile = os.path.abspath(os.path.join(new_profile, "..", old_add_on_id))
    xbmc.log("Retrospect: old Profile located at {}".format(old_profile), log_level)
    if not os.path.exists(old_profile):
        return

    d.notification(add_on_name, "Migrating add-on data to new format.", icon="info", time=5)

    xbmc.log("Retrospect: Migrating addon_data {} to {}".format(old_profile, new_profile), log_level)
    shutil.copytree(old_profile, new_profile, ignore=shutil.ignore_patterns("textures"))

    # If there were local setttings, we need to migrate those too so the channel ID's are updated.
    local_settings_file = os.path.join(new_profile, "settings.json")
    if not os.path.exists(local_settings_file):
        return

    xbmc.log("Retrospect: Migrating {}".format(local_settings_file), log_level)
    with io.open(local_settings_file, mode="rb") as fp:
        content = fp.read()
        settings = json.loads(content, encoding='utf-8')

    channel_ids = settings.get("channels", {})
    channel_settings = {}
    for channel_id in channel_ids:
        new_channel_id = channel_id.replace(old_add_on_id, add_on_id)
        xbmc.log("Retrospect: - Renaming {} -> {}".format(channel_id, new_channel_id), log_level)
        channel_settings[new_channel_id] = settings["channels"][channel_id]

    settings["channels"] = channel_settings
    with io.open(local_settings_file, mode='w+b') as fp:
        content = json.dumps(settings, indent=4, encoding='utf-8')
        fp.write(content)

    # fix the favourites
    favourites_path = os.path.join(new_profile, "favourites")
    if os.path.isdir(favourites_path):
        xbmc.log("Retrospect: Updating favourites at {}".format(favourites_path), log_level)
        for fav in os.listdir(favourites_path):
            # plugin://net.rieter.xot/
            fav_path = os.path.join(favourites_path, fav)
            xbmc.log("Retrospect: - Updating favourite: {}".format(fav), log_level)
            with io.open(fav_path, mode='r', encoding='utf-8') as fp:
                content = fp.read()

            content = content.replace("plugin://{}/".format(old_add_on_id),
                                      "plugin://{}/".format(add_on_id))
            with io.open(fav_path, mode='w+', encoding='utf-8') as fp:
                fp.write(content)

    xbmc.log("Retrospect: Migration completed.", log_level)
    return


# Check for the migration
migrate_profile(Config.profileDir, Config.addonId, Config.rootDir, Config.appName)
