# Retrospect - Public GIT Repository #
*Use at own risk*

This repository holds the main code for Retrospect. For more information of bug reporting please visit https://bitbucket.org/basrieter/xbmc-online-tv or http://www.rieter.net/content/.

## Installation of the Nightly versions ##
The installation comes down to putting the folders from the GIT repo in the Kodi add-on folder (very often: /home/<user>/.kodi/addons or c:\users\<user>\AppData\Roaming\Kodi\addons). The result should be that the *addons* folder now contains at least these folders:

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

### Via GIT ###
Clone the Nightly GIT repository directly into the Kodi Add-on folder. So don't put it in a subfolder:

```
git clone git@bitbucket.org:basrieter/xbmc-online-tv.git
```

### Via Download ###
Download the complete Nightly GIT repo and extract it into the Kodi Add-on folder.

# Updating the Nightly Repo #
### Via GIT ###
Pull latest changes into your clone (located in the Kodi Add-on folder). After that remove all existing `*.pyc` and `*.pyo` files within the Retrospect folders.

### Via Download ###
Download the complete Nightly GIT repo. Remove all existing Retrospect folders and extract the new ones it into the Kodi Add-on folder.

In both situation run Retrospect at least once before accessing the Retrospect add-on settings. The initial run might take longer than usual, as Retrospect is initialising some stuff and downloads artwork.

# ! Be advised ! #
Depending on what branch you are on, Kodi will or will not attempt to auto-update the Retrospect Add-on as soon as there is an official update available:

* Master: this branch contains the most recent Retrospect code files. It will always be one version ahead of the current release and will thus not update. You need to ```git pull``` the changes.
* Release-x.x.x: this branch contains the most recent stable and officially release Retrospect code files. It is the same version as can be found online and it will auto update via Kodi if an update is available.

# Copyrights and Licenses #
*See also: http://www.rieter.net/content/xot/license/.*

## Retrospect (Dual) License ##
Retrospect Framework by Bas Rieter is licensed under a Creative Commons Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. Files that belong to the Retrospect Framework have a disclaimer stating that they are licensed under the Creative Commons Attribution-Non-Commercial-No Derivative Works 3.0 Unported License.

All channels, skins and config.py (further called Retrospect Additions) are free software: you can redistribute it and/or modify it under the terms of the GNU General Public License version 3 as published by the Free Software Foundation. Retrospect Additions are distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with Retrospect Additions. If not, see [1]. Kodi Add-on packages containing modified code must be given a different add-on identification to prevent confusion with the official packages.
Distributing Retrospect

The official add-on packages that are currently available within the official Retrospect Repository may not be distributed via other channels than the official Retrospect Repository. Only the official Retrospect Respository (net.rieter.xot.respository) package itself may be distributed and/or included within other Kodi (super) repositories.

## Disclaimer ##
Retrospect or Rieter.net are not connected to or in any other way affiliated with Kodi, Team Kodi, or the Kodi Foundation. Furthermore, any software, addons, or products offered by Retrospect or Rieter.net will receive no support in official Kodi channels, including the Kodi forums and various social networks.

## Rules & Terms ##
As more and more people are starting to make channels for the Retrospect Framework, we want to lay out some rules and terms for the channels that we will host on this site. Please stick to them before asking us to post or link to them on the site:

 1. We, the Retrospect Framework team, are not responsible for any content that is displayed using the Retrospect Framework.
 1. We, the Retrospect Framework team, do not support any kind of Adult content for the Retrospect Framework nor will we host it on our servers.

