import os
import io
import json
import xbmc


def migrate_profile(new_profile, add_on_id, kodi_add_on_dir):
    """ Migrates the old user profile.

    :param str|unicode new_profile:     The new profile folder
    :param str|unicode add_on_id:       The new add-on id
    :param str|unicode kodi_add_on_dir: The Kodi add-on dir

    """

    old_add_on_id = "net.rieter.xot"

    if os.path.isdir(new_profile):
        return

    import shutil

    old_add_on_path = os.path.join(kodi_add_on_dir, "..", old_add_on_id)
    if os.path.isdir(old_add_on_path):
        xbmc.log("Removing add-on from {}".format(old_add_on_path), 1)
        shutil.rmtree(old_add_on_path)

    old_profile = os.path.join(new_profile, "..", old_add_on_id)
    if not os.path.exists(old_profile):
        return

    xbmc.log("Cloning {} addon_data to {}".format(old_add_on_id, add_on_id), 1)
    shutil.copytree(old_profile, new_profile, ignore=shutil.ignore_patterns("textures"))

    local_settings_file = os.path.join(new_profile, "settings.json")
    if not os.path.exists(local_settings_file):
        return

    xbmc.log("Migrating {} settings.json".format(add_on_id), 1)
    with io.open(local_settings_file, mode="rb") as fp:
        content = fp.read()
        settings = json.loads(content, encoding='utf-8')

    channel_ids = settings.get("channels", {})
    channel_settings = {}
    for channel_id in channel_ids:
        new_channel_id = channel_id.replace(old_add_on_id, add_on_id)
        xbmc.log("Renaming {} -> {}".format(channel_id, new_channel_id), 1)
        channel_settings[new_channel_id] = settings["channels"][channel_id]

    settings["channels"] = channel_settings
    with io.open(local_settings_file, mode='w+b') as fp:
        content = json.dumps(settings, indent=4, encoding='utf-8')
        fp.write(content)

    return
