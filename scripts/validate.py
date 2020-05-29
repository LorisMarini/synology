from imports import *
from helpers import extensions_and_types


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


def validate_args(arguments):

    # Check type
    for field in fields(arguments):
        value = getattr(arguments, field.name)
        if type(value) != field.type:
            message = f"Expected type {field.type} for {field.name}, got {type(value)}"
            raise TypeError(message)

    # Make sure dump is mounted
    check_dir(arguments.dump)

    # Make sure staging are mounted and accessible
    for key, value in arguments.server.items():
        check_dir(arguments.server[key])

    # Check mode is allowed
    allowed_modes = ["copy", "move"]
    if arguments.mode not in allowed_modes:
        raise ValueError(f"mode can be one of {allowed_modes}, passes {arguments.mode}")

    # Make sure staging and server direcotry keys match with file types
    # Get file types
    file_types = list(extensions_and_types()["file_type"].unique())

    # Get current staging keys
    staging_keys = list(arguments.staging.keys())
    staging_keys.remove("HOME")
    for k in staging_keys:
        if k not in file_types:
            raise ValueError(f"supported files types are {file_types}. "
                             f"Key {k} not supported in staging dict.")
