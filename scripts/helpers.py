from imports import *


def ls_recursive(*, src_dir:str, ignore=[]) -> List[str]:
    """
    Returns a list of absolute paths (str) of all objects
    inside src_dir. If ignore is passed, it drops all files
    containing any of the patterns to ignore.
    """
    # Search for all files recursively
    files = [name for name in glob.glob(f"{src_dir}/**/*.*", recursive=True)]
    print(f"{len(files)} total files found in src_dir")

    if ignore:
        files = pd.DataFrame(files, index=range(len(files)), columns=["files"])
        where = any_words_in_column(files, column="files", words=ignore, verbose=False)
        output = files.loc[~where, "files"].to_list()
        print(f"{where.sum()}/{len(files)} files ignored because contain one or more of {ignore}")
    else:
        output = files
    return output


def file_metadata(files:List[str]) -> pd.DataFrame:
    """
    Takes a list of absolute pahts to files on a mounted volume,
    and returns a table with file metadata.
    """
    # Collect file stats for each file
    file_stats = [os.stat(f) for f in files]
    print(f"{len(files)} files stats collected...")

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
    # Extract basenames
    basenames = [os.path.basename(f) for f in files]
    df["abspath_src"] = files
    df["basename_src"] = basenames

    # Add file anme and extension
    df["filename_src"] = df["basename_src"].apply(lambda x: os.path.splitext(x)[0])
    df["extension_src"] = df["basename_src"].apply(lambda x: os.path.splitext(x)[1])

    # Assume creation time is min(c_time, m_time)
    df["created_at"] = df[["st_mtime","st_ctime"]].min(axis=1)
    print(f"stats table built...")

    output = add_filetype(table=df)
    print(f"file types inferred...")

    return output


def add_filetype(*, table:pd.DataFrame) -> pd.DataFrame:
    """
    Expects two columns in table: "basename_src", "extension_src"
    """

    lookup = extensions_and_types()
    table["extension_src"] = table["extension_src"].str.lower()

    # Left join table with file_types
    output = pd.merge(table, lookup, how="left", left_on="extension_src", right_on="file_ext")

    missing = list(output[output["file_type"].isnull()]["extension_src"].unique())
    if missing:
        raise ValueError(f"Could not determine the file type for the following extensions {missing}.")

    return output


def extensions_and_types():
    """
    Builds a dataframe of known file extensions and their types (image, video, audio, archive).
    """
    image_ext = [".xmp", ".jpg", ".jpeg", ".png", ".gif", ".cr2", ".tif", ".bmp", ".psd"]
    image = list(zip(["image"]*len(image_ext), image_ext))

    video_ext = [".mp4", ".mov", ".avi", ".wmv", ".web"]
    video = list(zip(["video"]*len(video_ext), video_ext))

    audio_ext = [".mid",".mp3",".m4a",".ogg",".fla",".wav",".amr"]
    audio = list(zip(["audio"]*len(audio_ext), audio_ext))

    archive_ext = [".epub", ".zip",".tar",".gz",".bz2",".pdf",".exe",".ps",".sqlite"]
    archive =  list(zip(["archive"]*len(archive_ext), archive_ext))

    output = pd.DataFrame(image+video+audio+archive, columns=["file_type", "file_ext"])
    return output


def cli_ask_question(*, question:str, options:List[str]):
    """
    Prompts the user to answer a question with a range of possible answers.
    Keeps asking until it detects a valid answer (one of options).
    """
    invalid = True
    while invalid:
        answer = input(question)
        if answer in options:
            invalid = False
        else:
            print(f"\nInvalid answer, expected one of {options}")
            pass

    return answer


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


def clean_directory(path:str):

    dirs = glob.glob(f'{path}/*')
    for d in dirs:
        shutil.rmtree(d)

    print(f"{path} cleaned.")
