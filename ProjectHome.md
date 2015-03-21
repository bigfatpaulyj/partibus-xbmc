## About ##

Partibus is an [XBMC](http://www.xbmc.org) plugin that aims to improve the user experience for when multiple users want to queue content to be played on XBMC.

It aims to provide a "democratic" queueing system. This allows no one user to dominate what content is played on XBMC. It is particularly useful for parties where many people want to request music to be played. It also works for Video and Youtube videos.

## Example Usage ##
User 1 requests 4 tracks to be played. User 2 then requests his favourite song. The actual playback order would be as follows:

```
user 1, track 1
user 2, track 1
user 1, track 2
user 1, track 3
user 1, track 4
```

Without the Partibus plugin the order would have been as follows, and forces user-2 to have to wait for all user-1's tracks to complete first:

```
user 1, track 1
user 1, track 2
user 1, track 3
user 1, track 4
user 2, track 1
```

## User Interface ##
The [user interface](http://partibus.dyndns.org) is a [JQuery Mobile](http://jquerymobile.com/) based website. By making this a website rather than an app it provides maximum cross-platform support and is therefore particularly suitable to parties where there would be a mixture of mobiles/laptops etc.

![http://www.hostpic.org/images/1302041846270111.png](http://www.hostpic.org/images/1302041846270111.png)

## Main Features ##
  * "democratic" queueing system
  * web based frontend
  * "democratic" skip function. If at least 50% of the people at the party select skip, then the song will skip

## Current Status ##
Most of the development work is done but has not been tested much yet. Active development has ceased due shortage of time on my part. It is usable in it's current state however.

## How to Install ##
  * Download the XBMC plugin on the Downloads page.
  * Install the XBMC Plugin by going to System-->Add-ons-->"Install from zip file" and choosing the plugin you downloaded.
  * Go to the plugin settings within XBMC and configure the XBMC listen port to match you XBMC http listen port. Leave the plugin port at its default (19587).
  * Go to [http://partibus.dyndns.org](http://partibus.dyndns.org) and signup.
  * While logged into the site, add a new host on the Accounts tab. Choose the port to match what is configured in the plugin in XBMC (default 19857).
  * You should now be able to begin queueing tracks.

NOTE: the plugin doesn't start automatically within XBMC so you must start it manually from the Programs menu in XBMC. Alternatively, you can add it to the XBMC auto start script 'autoexec.py'.