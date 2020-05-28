#!/Users/lorismarini/anaconda3/bin/python

"""
This solves the problem of organizing content automatically
based on the date of creation, as well as loading it to the
server while keeping track of any errors thet might arise.
"""

from imports import *
from helpers import *
from validate import *


def default_staging_paths():

    staging_home = '/Users/lorismarini/ds918/staging'

    output = {"HOME": staging_home,
              "image": f"{staging_home}/image",
              "video": f"{staging_home}/video",
              "audio": f"{staging_home}/audio",
              "archive": f"{staging_home}/archive"}
    return output

def default_server_paths():

    server_home = '/Volumes'

    output = {"HOME": server_home,
              "image": f"{server_home}/photo",
              "video": f"{server_home}/video",
              "audio": f"{server_home}/photo",
              "archive": f"{server_home}/documents"}
    return output

def default_ignore():
    return ['.jsonl', '.json']


@dataclass(init=True, repr=True)
class Arguments:
    # Dump directory
    dump: str = field(default ='/Users/lorismarini/ds918/dump')
    # Staging directories
    staging: dict = field(default_factory = default_staging_paths)
    # server directories
    server: dict = field(default_factory = default_server_paths)
    # Any file extensions to ignore
    ignore: list = field(default_factory = default_ignore)
    # If existing files are found
    replace: bool = True
    # Migration mode
    mode: str = 'copy'


def migration_table(*, df: pd.DataFrame, dirs:dict) -> pd.DataFrame:
    """
    Extends a files table with two columns:
        - `dirname_dst` (absolute path to the destination directory)
        - `abspath_dst` (absolute of the file at destination)
    df should have:
        - basename_src:
        - filename_src:
        - extension_src:
        - created_at:
    """
    # Create basename of file at destination
    df = create_basename_dst(df)

    # Add column "dirname_dst"
    s = pd.Series(data=dirs, name="parentdir_dst")
    s.index.name="key"
    type_directory_map = s.to_frame().reset_index()
    df = pd.merge(df, type_directory_map, how="left",
                  left_on="file_type", right_on="key").drop(columns=["key"])

    # Name of the containing directory
    df["dirname_dst"] = df["parentdir_dst"] + "/" + df["created_at"].dt.date.astype(str)
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


def execute_migration(*, df:pd.DataFrame, mode:str, replace:str):

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

    print(tabulate(report_table, headers=list(report_table.columns)))


def stage(arguments:Arguments):

    # List files in src and ignore some
    files = ls_recursive(src_dir=arguments.dump, ignore=arguments.ignore)
    if len(files) == 0:
        return

    # Build a table of files metadata
    meta = file_metadata(files=files)

    # Build a migration table
    table = migration_table(df=meta, dirs=arguments.staging)
    if len(table) == 0:
        return

    # Execute first migration
    report = execute_migration(df=table, mode=arguments.mode,
                                     replace=arguments.replace)


def load(arguments:Arguments):

    print("Loading data to server...")

    # List files in src and ignore some
    files = ls_recursive(src_dir=arguments.staging["HOME"], ignore=arguments.ignore)

    # Build a table of files metadata
    meta = file_metadata(files=files)

    # Build a migration table
    table = migration_table(df=meta, dirs=arguments.server)
    if len(table) == 0:
        return

     # Execute migration
    report = execute_migration(df=table, mode=arguments.mode, replace=arguments.replace)


def main() -> None:

    # Instantiate default arguments object
    arguments = Arguments()

    # Validate and assign arguments to a global variable
    validate_args(arguments)

    # Prepare files to be loaded to server
    stage(arguments)

    staging_home = arguments.staging["HOME"]

    # Get user input
    options = ["y", "n"]
    question = (f"\nMigration settings are:"
                f"\n\treplace: {arguments.replace}"
                f"\n\tmode: {arguments.mode}"
                f"\nCheck {staging_home}:"
                f"\n\tDo you want to load data to the server? {'/'.join(options)}: ")

    answer_a = cli_ask_question(question=question, options=options)

    if answer_a == "y":
        # Actually load data on the server
        load(arguments)

        options = ["y", "n"]
        question = (f"\nDo you want to clean {staging_home}?")
        answer_b = cli_ask_question(question=question, options=options)

        if answer_b == "y":
            clean_directory(staging_home)
        else:
            print("Cleaning skipped.")
    else:
        print(f"load skipped. All files are ready to load in {staging_home}. Abortng.")


if __name__ == "__main__":
    main()
