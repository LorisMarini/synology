#!/Users/lorismarini/anaconda3/bin/python

"""
This solves the problem of organizing content automatically
based on the date of creation, as well as loading it to the
server while keeping track of any errors thet might arise.
"""

from imports import *
from helpers import *
from validate import *


@dataclasses.dataclass(init=True, repr=True)
class Arguments:
    dir_dump: str = '/Users/lorismarini/synology_stg/photo-videos/dump'
    dir_staging: str = '/Users/lorismarini/synology_stg/photo-videos/staging'
    dir_server = '/Volumes/photo'
    ignore = [".json", ".psd"]
    replace: bool = True
    mode: str = 'copy'


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

    # Guess file types
    output["file_type"] = [guess_file_type(p) for p in output["abspath_src"]]

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

        if os.path.exists(dst) and not replace:
            # If it already exists and we don't want to relace skip
            report["skipped"] = True

            print(f"File already exists in dst and replace={replace}. "
                  f"If you want to relace them pass replace=True")
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

    print(tabulate(report_table,headers='firstrow'))

    return report_table


def transform(arguments:Arguments):

    # List files in src and ignore some
    files = ls_recursive(src_dir=arguments.dir_dump, ignore=arguments.ignore)
    if len(files) == 0:
        return

    # Build a migration table
    table = migration_table(files=files, dst_dir=arguments.dir_staging)
    if len(table) == 0:
        return

    # Execute first migration
    report = execute_migration_table(df=table, mode=arguments.mode,
                                     replace=arguments.replace)


def load(arguments:Arguments):

    print("Loading data to server...")

    # List files in src and ignore some
    abspath_src = ls_recursive(src_dir=arguments.dir_staging, ignore=arguments.ignore)

    # Build new names
    abspath_dst = [p.replace(arguments.dir_staging, arguments.dir_server) for p in abspath_src]

    # Prepare table
    table=pd.DataFrame({"abspath_src": abspath_src, "abspath_dst": abspath_dst})

    # Execute first migration
    report = execute_migration_table(df=table, mode=arguments.mode,
                                     replace=arguments.replace)


def main() -> None:

    # Instantiate default arguments object
    arguments = Arguments()

    # Validate and assign arguments to a global variable
    validate_args(arguments)

    # Prepare files to be loaded to server
    transform(arguments)

    # Get user input
    options = ["y", "n"]
    question = (f"\nMigration settings are:"
                f"\n\treplace: {arguments.replace}"
                f"\n\tmode: {arguments.mode}"
                f"\nCheck {arguments.dir_staging}:"
                f"\n\tDo you want to load data to the server? {'/'.join(options)}: ")

    answer_a = cli_ask_question(question=question, options=options)

    if answer_a == "y":
        # Actually load data on the server
        load(arguments)

        options = ["y", "n"]
        question = (f"\nDo you want to clean {arguments.dir_staging}?")
        answer_b = cli_ask_question(question=question, options=options)

        if answer_b == "y":
            clean_directory(arguments.dir_staging)
        else:
            print("Cleaning skipped.")
    else:
        print(f"load skipped. All files are ready to load in {arguments.dir_staging}. Abortng.")


if __name__ == "__main__":
    main()
