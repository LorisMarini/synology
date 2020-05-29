![](images/etl-synology.png)

## What

A tool to organise my digital life from a dump folder to various drives on my home server (WIP).

### Problem

A zoo of devices generates content of different types, sizes, and naming and conventions that sit on various storage devices. To bring these to life, I built a home server. I would like:

1. dump all content in one folder
1. run a script
1. find all content neatly arranged on my server

### Demo

By default this reads from `./data/dump` which contains some sample files. A migration plan is prepared and executed (copy + rename) to separate images, videos, audio, and archives in corresponding subdirectories under `./data/staging`. Here is a demo:

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/tLQYUkjQG2A/0.jpg)](http://www.youtube.com/watch?v=tLQYUkjQG2A?start=6)

### Must Haves

From an arbitrarily-nested directories and file types, I want to:

1. **list** all files recursively
1. **timestamp** files based on creation time `_YYYY-MM-DD_H-M-S`
1. **fuzzy-search** time information in the file name
1. **deduplicate** files (filename + extension + creation time)
1. **organise** files in tree based on file type and creation date `YYYY-MM-DD`
1. **load** the new structure to my server
1. **handle** errors gracefully
1. **stage** files before loading to the final destination (optional)
1. **audit** data migration plans.

### Solution

Clone the repo, cd into it, and run:

`python run.py`

### How

A migration is made of two function calls:
- plan()
- execute()

`plan()`

Implements a migration plan and includes these steps:

1. Discover all files in dump
1. Build a table to describe them (name, extension, time, size, type)
1. Extend the table with information of where they should be moved to (migration table)

`execute()`

Takes the original absolute path of each file (abspath_src) and their new absolute path at the destination (abspath_dst).

**Under the hood**

Each file is then moved/copied, replacing/skipping depending on the global settings:

- `replace`: if True files with the same name are replaced
- `mode`: one of ['copy', 'move']. Choose 'copy' for idempotency.

File types are inferred form their extension (or suffix). [filetype](https://github.com/h2non/filetype.py) is a better option, but it's expensive for mounted folders over the network.


### Improvements

There are a number of easy fixes here:

1. The function `has_time_info` assumes that "-" is used to separate datetime parts, while "\_" is used as a separator (for example `FILE_20200101.jpg` is considered not to have time info).
1. I assume the creation time is the minimum between [ctime and mtime](https://www.gnu.org/software/coreutils/manual/html_node/File-timestamps.html). Next I might look at ways to read the creation time from the file metadata (with projects like [exif](https://pypi.org/project/exif/))
1. Ad warning when mode="copy" and the `dump` folder is over 5GB in size, and wait for user input to proceed.
1. Add tests

Constructive feedback is welcome, open an issue or submit a PR :D.
