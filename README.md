## What

Utilities to simplify my interaction with Synology 918. Pretty much a WIP, only tested on macOS.

### Problem
![](images/etl-synology.png)

A zoo of devices generates content of different types, sizes, and naming and conventions that sit on various storage devices. To bring these to life, I built a home server. I would like:

1. dump all content in one folder
1. run a script
1. find all content neatly arranged on my server

**Must Haves**

From an arbitrarily-nested directories and file types, I want to:

1. **list** all files recursively
1. determine their **creation time**
1. **ignore** names based on specific patterns (e.g. '.json' or '.psd')
1. **fuzzy-search** time information in the file name
1. **add timestamp** `_YYYY-MM-DD_H-M-S` to files that need it
1. deduplicate files (filename + extension + creation time)
1. organise files in tree based on file type and creation date `YYYY-MM-DD`
1. upload the new structure to my server
1. Graceful handling of errors and unexpected situations
1. Option to stage files before loading to the final destination
1. Option to inspect a migration plan to see what, why, and how it happened.

### Solution

Clone the repo, cd into it and run:

`python run.py`

**Example of tree**

```zsh
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
