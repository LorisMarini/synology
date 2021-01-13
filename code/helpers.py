from imports import *


def staging_paths(home:str) -> dict:

    output = {"HOME": home,
              "image": f"{home}/image",
              "video": f"{home}/video",
              "audio": f"{home}/audio",
              "archive": f"{home}/archive"}
    return output


def server_paths(home:str) -> dict:

    output = {"HOME": home,
              "image": f"{home}/photo",
              "video": f"{home}/video",
              "audio": f"{home}/photo",
              "archive": f"{home}/documents"}
    return output


@dataclass(init=True, repr=True)
class Arguments:
    # Dump directory
    dump: str
    # Staging directories
    staging: dict
    # server directories
    server: dict
    # Any file extensions to ignore
    ignore: list
    # If existing files are found
    replace: bool = False
    # Migration mode
    mode: str = 'copy'

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __str__(self):
        return (f"\nMigration settings:"
                f"\n  dump: {self.dump}"
                f"\n  staging_home: {self.staging['HOME']}"
                f"\n  server_home: {self.server['HOME']}"
                f"\n  ignore: {self.ignore}"
                f"\n  replace: {self.replace}"
                f"\n  mode: {self.mode}")

    def __post_init__(self):

        # Check types
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) != field.type:
                message = f"Expected type {field.type} for {field.name}, got {type(value)}"
                raise TypeError(message)

        # Make sure dump is mounted
        check_dir(self.dump)

        # Make sure server are mounted and accessible
        for key, value in self.server.items():
            check_dir(self.server[key])

        # Check mode is allowed
        allowed_modes = ["copy", "move"]
        if self.mode not in allowed_modes:
            raise ValueError(f"mode can be one of {allowed_modes}, passes {self.mode}")

        # Make sure staging and server direcotry keys match with file types
        file_types = list(extensions_and_types()["file_type"].unique())
        # Get keys used to map staging volumes
        staging_keys = [k for k in self.staging.keys() if k is not "HOME"]
        # Find keys that do not appear in file_types
        notmaching_keys = [k for k in staging_keys if k not in file_types]
        if notmaching_keys:
            raise ValueError(f"supported files types are {file_types}. "
                             f"Key {k} not supported in staging dict.")


def check_dir(path:str):

    if not os.path.isdir(path):
        raise ValueError(f"directory {path} not accessible "
                         f"or inexistent in the filesystem.")


def validate_staging(arguments):

    # Make sure staging are mounted and accessible
    for key, value in arguments.staging.items():
        try:
            check_dir(arguments.staging[key])
        except Exception as ex:
            if key == "HOME":
                raise ex
            else:
                # Make directory is staging
                os.makedirs(value, exist_ok=False)
                print(f"could not find directory {value}, just created one.")


def add_filetype(*, table:pd.DataFrame) -> pd.DataFrame:
    """
    Expects two columns in table: "basename_src", "extension_src"
    """

    lookup = extensions_and_types()
    table["extension_src"] = table["extension_src"].str.lower()

    # Left join table with file_types
    output = pd.merge(table, lookup, how="left", left_on="extension_src", right_on="file_ext")

    missing_types = output["file_type"].isnull()
    missing_types_tot = missing_types.sum()
    unknown_extensions = list(output.loc[missing_types, "extension_src"].unique())

    if missing_types_tot>0:
        Warning(f"Ignoring a total of {missing_types_tot} files with unknown extensions {unknown_extensions}.")
        output = output.dropna(axis=0, how="any",subset=["file_type"]).reset_index(drop=True)

    return output


def extensions_and_types():
    """
    Builds a dataframe of known file extensions and their types (image, video, audio, archive).
    """
    image_ext = [".xmp", ".jpg", ".jpeg", ".png", ".gif", ".cr2",
                 ".tif", ".bmp", ".psd", ".ico", ".svg", ".thm", ".tiff"]

    video_ext = [".mp4", ".mov", ".avi", ".wmv", ".wav",".web", ".mpg", ".swf", ".cmproj"]
    audio_ext = [".mid",".mp3",".m4a",".ogg",".fla",".wav",".amr", ".nhzx"]

    archive_ext = [".txt", ".epub", ".zip",".tar",".gz",".bz2",".pdf",".exe",".ps",".sqlite",
                   ".doc",".docx",".xls",".xlsx",".ppt",".pptx",".odt",".ods",".odp",
                   ".rtf"]

    image = list(zip(["image"]*len(image_ext), image_ext))
    video = list(zip(["video"]*len(video_ext), video_ext))
    audio = list(zip(["audio"]*len(audio_ext), audio_ext))
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


def create_basename_dst(df:pd.DataFrame) ->pd.DataFrame:
    """
    Creates the column `basename_dst`, based on original
    filename (`filename_src`) and extension (`extension_src`),
     as well as a timestamp if `filename_src` does not contain
     time info.
    """

    df["basename_dst"] = None

    # Determine if there is time information in the basename
    has_time = df["basename_src"].apply(has_time_info)

    # Append time to those that don't have it
    where = has_time == False
    # Build new name
    n = df.loc[where, "filename_src"]
    e = df.loc[where, "extension_src"]
    t = df["created_at"].dt.strftime("%Y%m%d_%H%M%S")[where]
    df.loc[where, "basename_dst"] = n + "_" + t + e

    # Preserve name if it has time info
    df.loc[has_time == True, "basename_dst"] = df.loc[has_time == True, "basename_src"]

    if df["basename_dst"].count() < df.shape[0]:
        raise ValueError("Some files are missing a destination basename.")

    return df


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
