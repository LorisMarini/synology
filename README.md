## What

Utilities to simplify my interaction with Synology 918.

## Scripts

#### etl-photos-videos.py

![](images/etl-synology.png)

This solves the problem of organising content automatically based on the date of creation, as well as loading it to the server while keeping track of any errors that might arise.

Behaviour is controlled through four attributes:
- dir_dump: where I occasionally dump files to load to the server (GoPro, Canon, other)
- dir_staging: where files are renamed, deduped, and arranged in a tree before being moved
- dir_server: where I want these files to go
- replace: if True files with the same name are overritten
- mode: one of ['copy', 'move']. Choose 'copy' for idempotent behaviour.

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
