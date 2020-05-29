from imports import *
from helpers import *


def plan(*, source:str, destinations:dict, ignore:bool) -> pd.DataFrame:
    """
    From
    """
    print("Building a migration plan...")

    # List files in src and ignore some
    files = ls_recursive(src_dir=source, ignore=ignore)
    if len(files) == 0:
        return

    # describe files (string ops, fast)
    shallow = filedesc_shallow(files=files)

    # grub stats for each file (slower)
    deep = filedesc_deep(files=files)

    # Combine
    description = pd.merge(shallow, deep, how="outer", on="abspath_src")

    # Build a migration table
    table = migration_table(df=description, dirs=arguments.server)
    print("Plan ready.")

    return table


def ls_recursive(*, src_dir:str, ignore=[]) -> List[str]:
    """
    Returns a list of absolute paths (str) of all objects
    inside src_dir. If ignore is passed, it drops all files
    containing any of the patterns to ignore.
    """
    # Search for all files recursively
    print("Listing all files recursively...")
    files = []
    iterator = glob.iglob(f"{src_dir}/**/*.*", recursive=True)
    for fn in tqdm(iterator):
        files.append(fn)

    if ignore:
        files = pd.DataFrame(files, index=range(len(files)), columns=["files"])
        where = any_words_in_column(files, column="files", words=ignore, verbose=False)
        output = files.loc[~where, "files"].to_list()
        print(f"{where.sum()}/{len(files)} files ignored because contain one or more of {ignore}")
    else:
        output = files

    print(f"{len(files)} total files found in src_dir")
    return output


def filedesc_shallow(files:List[str]) -> pd.DataFrame:
    """
    Returns a table with basename, extension and file type as inferred
    by looking at the extension. All string operations, really fast.
    """
    # Extract basenames
    df = pd.DataFrame()
    df["abspath_src"] = files
    df["basename_src"] = [os.path.basename(f) for f in files]

    # Add file anme and extension
    df["filename_src"] = df["basename_src"].apply(lambda x: os.path.splitext(x)[0])
    df["extension_src"] = df["basename_src"].apply(lambda x: os.path.splitext(x)[1])
    df["extension"] = df["extension_src"].str.lower()

    # Left join table with file_types
    lookup = extensions_and_types()
    output = pd.merge(df, lookup, how="left", left_on="extension", right_on="file_ext")

    missing_types = output["file_type"].isnull()
    missing = missing_types.sum()
    unknown_extensions = list(output.loc[missing_types, "extension"].unique())

    if missing>0:
        print(f"WARNING: {missing} files with unknown extensions {unknown_extensions}.")

    return output


def filedesc_deep(files:List[str]) -> pd.DataFrame:
    """
    Takes a list of absolute pahts to files on a mounted volume,
    and returns a table with file stats like ctime, mtime, size...
    Requires file system access, and may be slow on a remote drive.
    """

    # Collect file stats for each file
    file_stats = [os.stat(f) for f in files]

    # Unpack metrics. Full list of metrics at:
    # https://docs.python.org/3.8/library/os.html#os.stat_result.st_size
    all_stats = [{"st_mtime": int(fstats.st_mtime),
                  "st_ctime": int(fstats.st_ctime),
                  "st_size": int(fstats.st_size)} for fstats in file_stats]

    # Build a table
    df = pd.DataFrame(all_stats)
    # Cast datetimes
    df["st_mtime"] = pd.to_datetime(df["st_mtime"], unit="s")
    df["st_ctime"] = pd.to_datetime(df["st_ctime"], unit="s")
    df["abspath_src"] = files

    # Assume creation time is min(c_time, m_time)
    df["created_at"] = df[["st_mtime","st_ctime"]].min(axis=1)

    return df


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
    print(f"{is_duplicate.sum()}/{len(df)} files ignored because duplicated")

    # Drop files with missing file_type
    unknowns = output["file_type"].isnull().sum()
    output = output.dropna(axis=0, how="any",subset=["file_type"]).reset_index(drop=True)
    print(f"{unknowns}/{len(df)} files ignored because extensions not recognized")

    print(f"{output.shape[0]}/{len(df)} files to migrate.")

    if output.shape[0] > 0:
        print("\nExample of migration table:")
        print(output.iloc[0].T)
        print("\n")

    return output
