## What

Utilities to simplify my interaction with Synology 918. Pretty much a WIP, only tested on macOS.

## Scripts

#### Problem
I take photos and videos with various devices in different moments in time. Each device names and organises files differently. I want to dump all of them in a directory (call it `dump`) and find them *well organised* in my Synology mount point (a RAID6 volume with integrity protection, automatically indexed and used by both DSPhotos and Moments to manage my digital memories).

![](images/etl-synology.png)


From an arbitrarily-nested directories and files, the script should:

1. **list** recursively inside `dump`
1. determine the **creation time** of each file
1. **ignore** files containing specific patterns (e.g. '.json' or '.psd')
1. **fuzzy-search** time information in the file name
1. **add timestamp** `_YYYY-MM-DD_H-M-S` to files that need it
1. deduplicate files (by basename and creation time)
1. organise files in folders named after the date of creation `YYYY-MM-DD`.
1. upload this new structure to my Synology volume

**Features**
1. Graceful handling of errors and unexpected situations
1. Stage the new file structure in `staging` before transferring files to the server (relatively slow)
1. Audit each migration plan to see what, why, and how it happened.

**Example of tree**

```
    ├── dump
    │   ├── test_upload.json
    │   ├── VID_20190513_211732488.mp4
    │   ├── business_id_test.jsonl
    │   ├── dir
    │   |   └── IMG_5712-2.jpg
    │   ├── dir2
    │       └── dir3
    │           └── wedding_primo_ballo.mp4
    └── staging
        ├── 2015-10-04
        │   └── IMG_5712-2_20151004_013542.jpg
        ├── 2019-08-28
        │   └── wedding_primo_ballo_20190828_072354.mp4
        └── 2019-09-07
            └── VID_20190513_211732488.mp4
```

#### Solution

`python etl-photos-videos.py`

**Parameters**

The script behaviour can be changed with 2 attributes:

- `replace`: if True files with the same name are overritten
- `mode`: one of ['copy', 'move']. Choose 'copy' for idempotency.

Modify this part of the script accordingly:
```
dir_dump: str = '/Users/lorismarini/synology_stg/photo-videos/dump'
dir_staging: str = '/Users/lorismarini/synology_stg/photo-videos/staging'
dir_server = '/Volumes/photo'
replace: bool = True
mode: str = 'copy'
```

**Screenshots**
First invocation:
![](images/screenshot1.png)

The script returns a report with details of each migration from `dump` to `staging`
![](images/screenshot2.png)

When the files in `staging` are ready we should check that everything looks right. The last step is to load data to the server:
![](images/screenshot3.png)
