**Parameters**

The script behaviour can be changed with 2 attributes:

- `replace`: if True files with the same name are overritten
- `mode`: one of ['copy', 'move']. Choose 'copy' for idempotency.

Modify this part of the script accordingly:

```python
dir_dump: str = '/Users/lorismarini/synology_stg/photo-videos/dump'
staging_dirs: str = '/Users/lorismarini/synology_stg/photo-videos/staging'
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

**Quick Improvements**

There are a number of easy fixes here:

1. The script does not distinguish between photos and videos. Should it separate the two? Maybe.
1. The function `has_time_info` assumes that "-" is used to separate datetime parts, while "\_" is used as a separator. The result is that the filename `FILE_20200101.jpg` is considered not to have time info.
1. I assume the creation time is the minimum between [ctime and mtime](https://www.gnu.org/software/coreutils/manual/html_node/File-timestamps.html), which is a big assumption. Next I might look at ways to read the creation time from the file metadata (with projects like [exif](https://pypi.org/project/exif/))
1. Ad warning when mode="copy" and the `dump` folder is over 5GB in size, and wait for user input to proceed.
1. Add tests
