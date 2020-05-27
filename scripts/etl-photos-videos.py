#!/Users/lorismarini/anaconda3/bin/python

"""
This solves the problem of organizing content automatically 
based on the date of creation, as well as loading it to the 
server while keeping track of any errors thet might arise.
"""

import os
import sys
import glob
import shutil
import dataclasses
import pandas as pd
from typing import List, Any
from tqdm import tqdm

USAGE = (f"Usage: python {sys.argv[0]} [--help] | ['/path/to/dir_dump'] "
         f"['/path/to/dir_staging'] ['/path/to/dir_server'] ['True'] ['copy']")

@dataclasses.dataclass(init=True, repr=True)
class Arguments:
    dir_dump: str = '/Users/lorismarini/synology_stg/photo-videos/dump'
    dir_staging: str = '/Users/lorismarini/synology_stg/photo-videos/staging'
    dir_server = '/Volumes/photo'
    replace: bool = True
    mode: str = 'copy'

def validate_args(args: List[str]):

    global arguments

    try:
        arguments = Arguments(*args)
    except TypeError:
        raise SystemExit(USAGE)

    # Check type
    for field in dataclasses.fields(arguments):
        value = getattr(arguments, field.name)
        if type(value) != field.type:
            message = f"Expected type {field.type} for {field.name}, got {type(value)}"
            raise TypeError(message)

    # Make sure dir_dump is mounted
    if not os.path.isdir(arguments.dir_dump):
        raise ValueError(f"Make sure that the directory src={arguments.dir_dump} "
                         f"is mounted and accessible in the filesystem.")

    # Make sure dir_staging is mounted
    if not os.path.isdir(arguments.dir_staging):
        raise ValueError(f"Make sure that the directory dst={arguments.dir_staging}"
                         f" is mounted and accessible in the filesystem.")

    allowed_modes = ["copy", "move"]
    if arguments.mode not in allowed_modes:
        raise ValueError(f"mode can be one of {allowed_modes}, passes {arguments.mode}")


def any_words_in_column(df, column, words, verbose=True):

    if not isinstance(df, pd.DataFrame):
        raise ValueErorr(f"df expected to be a pandas DataFrame, found {type(df)}")

    if not isinstance(words, list):
        raise ValueErorr(f"mapping expected to be a list, found {type(words)}")

    if not isinstance(verbose, bool):
        raise ValueErorr(f"verbose expected to be a boolean, found {type(verbose)}")

    if column not in df.columns:
        raise ValueErorr(f"column not found in dataframe")

    filters = [df[column].str.contains(w) for w in words]

    # Build a DataFrame with all the boolean series
    filters_table = pd.DataFrame(filters).T

    # Apply the "or" function along the columns
    where = filters_table.any(axis=1)

    if verbose:
        print(f"found {where.sum()} entries - or {round(where.sum()/len(where)*100, 1)}%")
    return where


def has_time_info(basename:str) -> bool:
    """
    Determine if there is time information in the basename.
    It uses pd.to_datetime() to try and parse a timestamp from the name.
    """
    bn = os.path.splitext(basename)[0].replace("_", " ")
    parts = bn.split(" ")
    parts.append(bn)
    
    any_time = pd.Series([pd.to_datetime(p, errors="coerce") for p in parts])
    if any_time.dropna().shape[0] > 0:
        output = True
    else:
        output = False
    return output


def ls_files(*, src_dir:str, recursive=True, ignore=[".json", ".psd"]) -> List[str]:
    
    # Search for all files recursively
    files = [name for name in glob.glob(f"{src_dir}/**/*.*", recursive=recursive)]
    print(f"{len(files)} total files found in src_dir")

    files = pd.DataFrame(files, index=range(len(files)), columns=["files"])
    where = any_words_in_column(files, column="files", words=ignore, verbose=False)
    output = files.loc[~where, "files"].to_list()

    print(f"{where.sum()}/{len(files)} files ignored because contain one or more of {ignore}")

    return output


def migration_table(*, files: List, dst_dir:str) -> pd.DataFrame:

    # Extract basenames of files to keep
    basenames = [os.path.basename(f) for f in files]

    # files_all
    file_stats = [os.stat(f) for f in files]
    print(f"{len(files)} files stats collected...")

    # Collect file stats for each file
    all_stats = [{"st_mtime": int(fstats.st_mtime), "st_ctime": int(fstats.st_ctime)} for fstats in file_stats]

    # Build table
    df = pd.DataFrame(all_stats)
    df["abspath_src"] = files
    df["basename_src"] = basenames

    # Parse times as datetime objects
    df["st_mtime"] = pd.to_datetime(df["st_mtime"], unit="s")
    df["st_ctime"] = pd.to_datetime(df["st_ctime"], unit="s")

    # Take the minimum of c_time and modified time as the creation time
    df["created_at"] = df[["st_mtime","st_ctime"]].min(axis=1)
    df["created_at_string"] = df["created_at"].dt.strftime("%Y%m%d_%H%M%S")
    print(f"stats table built...")

    # Determine if there is time information in the basename
    df["has_time_in_basename"] = df["basename_src"].apply(has_time_info)

    # Append time to those that don't have it
    where = df["has_time_in_basename"] == False
    original_name = df.loc[where, "basename_src"].str.split(".").str[0] 
    sep = "_"
    timestring = df.loc[where, "created_at_string"]
    original_ext = df.loc[where, "basename_src"].str.split(".").str[1]
    df.loc[where, "basename_dst"] = original_name + sep + timestring + "." + original_ext

    # Preserve name if it has time info
    where = df["has_time_in_basename"] == True
    df.loc[where, "basename_dst"] = df.loc[where, "basename_src"]

    # Name of the containing directory
    dirname = df["created_at"].dt.date.astype(str)
    df["dirname_dst"] = dst_dir + "/" + dirname
    df["abspath_dst"] = df["dirname_dst"] + "/" + df["basename_dst"]

    # Deduplicate files based on the destination basename (includes timestamp)
    is_duplicate = df.duplicated(subset=["basename_dst"], keep="first")
    output = df[~is_duplicate].reset_index(drop=True)

    print(f"\n{is_duplicate.sum()}/{len(df)} files duplicated and ignored"
          f"\n{output.shape[0]} total files to migrate...")

    if output.shape[0] > 0:
        print("\nExample of migration table:")
        print(output.iloc[0].T)
        print("\n")

    return output


def consolidate_dest_dirs(*, df:pd.DataFrame):

    # Create destination directories if they don't exist
    dirname_dest_unique = df["dirname_dst"].unique()

    # Create directories if they don't exist
    _ = [os.makedirs(d, exist_ok=True) for d in dirname_dest_unique]

    print(f"{len(dirname_dest_unique)} directories consolidated...")


def migrate_file(*, src:str, dst:str, mode:str, replace:bool) -> dict:

    report = {"src": os.path.basename(src), 
              "dst": os.path.basename(dst), 
              "copied": False, 
              "moved": False, 
              "skipped": False, 
              "error": None}

    try:
        if not os.path.exists(src):
            message = f"DATA INTEGRITY: File {src} expected but not found. Skipping"
            raise ValueError(message)

        # If it already exists and we don't want to relace skip
        if os.path.exists(dst) and not replace:
            print(f"File already exists in dst and replace={replace}. If you want to relace them pass replace=True")
            report["skipped"] = True
        else:
            # File in src exists
            if mode =="copy":
                # copy file preserving metadata
                # https://docs.python.org/3/library/shutil.html#shutil.copy2
                shutil.copy2(src, dst)
                report["copied"] = True
            elif mode =="move":
                # Move file preserving metadata
                # https://docs.python.org/3/library/shutil.html#shutil.move
                shutil.move(src, dst, copy_function=shutil.copy2)
                report["moved"] = True
            else:
                message = f"Migration mode {arguments.mode} not supported."
                raise ValueError(message)

    except Exception as ex:
        report["error"] = str(ex)
    return report


def execute_migration_table(*, df:pd.DataFrame, mode:str, replace:str):


    # Create destination directories if they don't exist
    dst_dirs = df["abspath_dst"].apply(lambda x: os.path.dirname(x))
    dst_dirs_unique = dst_dirs.unique()
    _ = [os.makedirs(d, exist_ok=True) for d in dst_dirs_unique]

    reports = []

    # tqdm wraps the iterable and roduces a progress bar
    for i in tqdm(df.index):

        # Get src and dst directories
        src = df.loc[i,"abspath_src"]
        dst = df.loc[i,"abspath_dst"]

        # Migrate file
        report = migrate_file(src=src, dst=dst, mode=mode, replace=replace)
        reports.append(report)

    # Build a table of migrations                
    report_table = pd.DataFrame(reports)
    copied = report_table["copied"].sum()
    moved = report_table["moved"].sum()
    skipped = report_table["skipped"].sum()
    error = report_table["error"].count()

    print(f"\nMigration complete. Report:"
          f"\n{copied} files copied"
          f"\n{moved} files moved"
          f"\n{skipped} files skipped"
          f"\n{error} errors")

    print(report_table)

    return report_table 
    

def transform():

    # List files in src and ignore some
    files = ls_files(src_dir=arguments.dir_dump, recursive=True)
    if len(files) == 0:
        return
    
    # Build a migration table
    table = migration_table(files=files, dst_dir=arguments.dir_staging)
    if len(table) == 0:
        return

    # Execute first migration
    report = execute_migration_table(df=table, mode=arguments.mode, 
                                     replace=arguments.replace)


def load():

    print("Loading data to server...") 
    
    # List files in src and ignore some
    abspath_src = ls_files(src_dir=arguments.dir_staging, recursive=True)
    
    # Build new names
    abspath_dst = [p.replace(arguments.dir_staging, arguments.dir_server) for p in abspath_src]

    # Prepare table
    table=pd.DataFrame({"abspath_src": abspath_src, "abspath_dst": abspath_dst})

    # Execute first migration
    report = execute_migration_table(df=table, mode=arguments.mode, 
                                     replace=arguments.replace)


def main() -> None:

    # Extract arguments
    args = sys.argv[1:]

    # Optionally print usage if required
    if args and args[0] == "--help":
        print(USAGE)
        return

    # Validate and assign arguments to a global variable
    validate_args(args)

    # Prepare files to be loaded to server
    transform()

    # Get user input
    invalid = True
    while invalid:
        ack = input(
                    f"\nMigration settings are:" 
                    f"\n\treplace: {arguments.replace}"
                    f"\n\tmode: {arguments.mode}"
                    f"\nCheck {arguments.dir_staging}:"
                    f"\n\tDo you want to load data to the server? y/n: ")
        if ack in(["y", "n"]):
            invalid = False

    if ack == "y":
        # Actually load data on the server
        load()

        dirs = glob.glob(f'{arguments.dir_staging}/*')
        for d in dirs:
            shutil.rmtree(d)

if __name__ == "__main__":
    main()

