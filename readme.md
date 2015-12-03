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
