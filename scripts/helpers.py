from imports import *


def guess_file_type(path:str):
    kind = filetype.guess(path)
    if kind:
        return kind.mime.split("/")[0]
    else:
        return None

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
