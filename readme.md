# Retrospect - Public GIT Repository #

This repository holds the main code for Retrospect. For more information of bug reporting please visit https://bitbucket.org/basrieter/xbmc-online-tv or https://www.rieter.net/content/.

# Installing Retrospect #
There are a couple of ways to install and/or update Retrospect using this GIT repository:

### 1 - Installing and updating Retrospect the 'Easy way' ###
If a `net.rieter.xot-x.x.x.zip` is available from the download section, this zip can be installed using Kodi's _Install from ZIP_ feature. Keep in mind that you these zip files may not always be up-to-date.

This method can also be used to install new versions of Retrospect and thus upgrading older installs.  

### 2 - Installation of Retrospect the 'Advanced way' ###
The installation comes down to putting the folders from the GIT repo (either via a _'GIT Clone'_ or _'Full Zip Download'_)in the Kodi add-on folder (very often: /home/<user>/.kodi/addons or c:\users\<user>\AppData\Roaming\Kodi\addons). The result should be that the *addons* folder now contains at least these folders:

```
 net.rieter.xot
 net.rieter.xot.channel.be
 net.rieter.xot.channel.mtg
 net.rieter.xot.channel.mtv
 net.rieter.xot.channel.nick
 net.rieter.xot.channel.no
 net.rieter.xot.channel.nos
 net.rieter.xot.channel.regionalnl
 net.rieter.xot.channel.rtlnl
 net.rieter.xot.channel.sbsnl
 net.rieter.xot.channel.se
 net.rieter.xot.channel.streams
 net.rieter.xot.channel.uk
 net.rieter.xot.channel.videos
```

#### Option A - ....via 'GIT Clone' ####
Clone the Nightly GIT repository into a folder of your choice:

```
git clone https://bitbucket.org/basrieter/xbmc-online-tv.git
```

The cloned GIT repository should contain the folders mentioned above. Now either `copy` or `symlink` (`junction` on Windows) each those folders into the Kodi Add-ons folder. I would suggest using symlinks or junctions so changes from a `git pull` are automatically available in Kodi. 

#### Option B - ....via 'Full Zip Download' ####
Download the complete GIT repo and extract it into the Kodi Add-on folder.

#### Caution!
Be aware that if you install it using *Option A* or *Option B* Kodi will **disable** the add-on by default and it will **not install any of the dependencies**. So you need to enable it manually and install all the dependencies by hand. Starting from Kodi Leia this is easier as it has a "View Dependencies" option of add-ons.   


### 3 - Updating Retrospect ###

#### Option A - ....via 'GIT Clone' ####
Pull latest changes into your clone (located in the Kodi Add-on folder). After that remove all existing `*.pyc` and `*.pyo` files within the Retrospect folders (**don't skip this**).

#### Option B - ....via 'Full Zip Download' ####
Download the complete GIT repo. Remove all existing Retrospect folders (**don't skip this**) and extract the new ones it into the Kodi Add-on folder.

#### Finalizing the update ####
In both situation run Retrospect at least once before accessing the Retrospect add-on settings. The initial run might take longer than usual, as Retrospect is initialising some stuff and downloads artwork.

# ! Be advised ! #
Retrospect will NOT auto-upate. So new version need to be installed manually. 

# Troubleshooting #

### Playing Widevine DRM content ###
Starting with Kodi Leia (Kodi 18) the playback of DRM protected streams is supported using the `input.adaptive` add-on. Kodi comes with this pre-installed, but by default it is disabled. So make sure that you **enable** it first. In order to play Widevine DRM files you will need to have the Google Widevine libraries installed. Android based devices have this as a native component, for Windows and Linux you will need to install them:

1. Determine the last version of the Widevine libraries: [https://dl.google.com/widevine-cdm/current.txt](https://dl.google.com/widevine-cdm/current.txt)
1. Download the appropriate version for your OS/Kodi combination (replace the {version} with the most recent version):
    * 32-bit kodi on Windows: [https://dl.google.com/widevine-cdm/{version}-win-ia32.zip](https://dl.google.com/widevine-cdm/{version}-win-ia32.zip)
    * 64-bit kodi on Windows: [https://dl.google.com/widevine-cdm/{version}-win-x64.zip](https://dl.google.com/widevine-cdm/{version}-win-x64.zip)
    * 32-bit kodi on Linux: [https://dl.google.com/widevine-cdm/{version}-linux-ia32.zip](https://dl.google.com/widevine-cdm/{version}-linux-ia32.zip)
    * 32-bit kodi on Linux: [https://dl.google.com/widevine-cdm/{version}-linux-x64.zip](https://dl.google.com/widevine-cdm/{version}-linux-x64.zip)
1. For Windows installation copy these files into your `<kodi-profile>\cdm` folder. Linux users need to install them manually (or they can use this [gist](https://gist.github.com/ruario/3c873d43eb20553d5014bd4d29fe37f1) ([Fork](https://gist.github.com/basrieter/44a463a97a60958c36435d54d50debb4)) to install it automatically).

_Example:_
> If the most recent version obtained via https://dl.google.com/widevine-cdm/current.txt is `1.4.9.1088`, then the download url for 64-bit windows is https://dl.google.com/widevine-cdm/1.4.9.1088-win-x64.zip.

The kodi.log will tell you if you did not put them in the correct place or if you have copied the wrong version.

_NOTE: for Kodi Krypton it seems that version 1.4.8.1008 is the last version that is compatible._

For **ARM Devices** things might be a bit different. If you are running Android, you probably don't need to do anything at all and Widevine should work. However, if you are running Linux on ARM there is a different approach:

1. Determine the last version of the libraries for ARM using this url: [https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.conf](https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.conf)
1. From that configuration file, find the image for an ARM device that resembles your device. 
    * Multiple successes have been reported using the the *Acer Chromebook R13* image.
    * The device configuration section in the config file have an `url` field that contains a link to a recovery image. 
    * In the case of the *Acer Chromebook R13* you can download the full recovery from this url: [https://dl.google.com/dl/edgedl/chromeos/recovery/chromeos_{version}_elm_recovery_stable-channel_mp.bin.zip](https://dl.google.com/dl/edgedl/chromeos/recovery/chromeos_11021.81.0_elm_recovery_stable-channel_mp.bin.zip).
1. From that recovery image you will need the Widevine files located in `/opt/google/chrome/libwidevinecdm*.so`.
1. These files need to be copied to the `<kodi-profile>/cdm` folder.

_NOTE: Keep in mind that you might need to try multiple recovery images before you find a working one._ 

# Copyrights and Licenses #
*See also: http://www.rieter.net/content/xot/license/.*

### Retrospect (Dual) License ###
Retrospect Framework by Bas Rieter is licensed under a Creative Commons Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. Files that belong to the Retrospect Framework have a disclaimer stating that they are licensed under the Creative Commons Attribution-Non-Commercial-No Derivative Works 3.0 Unported License.

All channels, skins and config.py (further called Retrospect Additions) are free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation. Retrospect Additions are distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with Retrospect Additions. If not, see [1]. Kodi Add-on packages containing modified code must be given a different add-on identification to prevent confusion with the official packages.
Distributing Retrospect

The official add-on packages that are currently available within the official Retrospect Repository may not be distributed via other channels than the official Retrospect Repository. Only the official Retrospect Respository (net.rieter.xot.respository) package itself may be distributed and/or included within other Kodi (super) repositories.

### Disclaimer ###
Retrospect or Rieter.net are not connected to or in any other way affiliated with Kodi, Team Kodi, or the Kodi Foundation. Furthermore, any software, addons, or products offered by Retrospect or Rieter.net will receive no support in official Kodi channels, including the Kodi forums and various social networks.

### Rules & Terms ###
As more and more people are starting to make channels for the Retrospect Framework, we want to lay out some rules and terms for the channels that we will host on this site. Please stick to them before asking us to post or link to them on the site:

 1. We, the Retrospect Framework team, are not responsible for any content that is displayed using the Retrospect Framework.
 1. We, the Retrospect Framework team, do not support any kind of Adult content for the Retrospect Framework nor will we host it on our servers.

