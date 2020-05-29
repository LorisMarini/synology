#! /Users/lorismarini/anaconda3/bin/python
"""
This Script assumes that the server has multiple volumes, each
corresponding to one of four file types, and mounted on different
points on /Volumes.

On macOS:
1. locate the internal (LAN) IP address <my.ip.addr.ess> of yor server (e.g. 192.168.1.110)
2. From finder 'cmd + K' and type 'afp://<my.ip.addr.ess>'. Replace 'afp' with 'smb' to user Samba3.
3. Authenticate with userbame and pw and you should see the volume mounted
4. You should see the four volumes: for me are:
    - /Volums/photo
    - /Volums/video
    - /Volums/photo
    - /Volums/documents

If you get lazy write a script that does this for you.
"""

from imports import *
from validate import *
from helpers import *
from plan import *
from execute import *

def main() -> None:

    # dump
    dump = "/Volumes/homes/Loris/Drive/Moments"
    staging_home = ""
    server_home = "/Volumes"
    ignore = []
    replace = False
    mode = 'move'
    staging = {}
    server = {"HOME": server_home,
              "image": f"{server_home}/photo",
              "video": f"{server_home}/video",
              "audio": f"{server_home}/photo",
              "archive": f"{server_home}/documents"}

    arguments = Arguments(dump, staging, server, ignore, replace, mode)

    # EXPENSIVE OPERATION: List files
    files = ls_recursive(src_dir=arguments.dump, ignore=arguments.ignore)

    # Select only video files
    keep = ['.3gp', '.mp4', '.MP4', '.mov', '.MOV', '.MPG', '.AVI', '.WAV', '.wav']
    files_to_move = list(pd.Series([f for f in files if os.path.splitext(f)[1] in keep]))

    # Find extensions of files to keep
    leave = pd.Series([os.path.splitext(f)[1] for f in files if os.path.splitext(f)[1] not in keep]).unique()

    # Build a table of files metadata
    meta = file_metadata(files=files_to_move)

    # Build a migration table
    table = migration_table(df=meta, dirs=arguments.server)
    print("Plan ready.")

    # Execute plan
    execute(df=table, mode=arguments.mode, replace=arguments.replace)


if __name__ == "__main__":
    main()
