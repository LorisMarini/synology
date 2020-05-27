## What

Utilities to simplify my interaction with Synology 918. Pretty much a WIP, only tested on macOS.

### Problem 1
![](images/etl-synology.png)

I take photos and videos with various devices in different moments in time. Each device names and organises files differently. I want to dump all of them in a directory (call it `dump`) and find them *well organised* in my Synology mount point (a RAID6 volume with integrity protection, automatically indexed and used by both DSPhotos and Moments to manage my digital memories).

### Solution 1

`python etl-syn.py`

Details [here](./ETL-SYNOLOGY.md).

### Problem 2

As part of the project of De-Googling myself I had to [export](https://takeout.google.com/settings/takeout?pli=1) my memories from Google Photos and load it back to my Synology. However, exports have:
1. metadata that I might want to drop
1. inconsistent names (my library spans many smartphone generations with Android and iOS)
1. directories have weird names (a consequence of file segmentation and a 2GB download limit)

I want to automate this.

### Solution 2

The notebook `remove_gphoto_metadata` has some notes. I did not put it into a script yet cause it's [not worth it now](https://xkcd.com/1205/).
