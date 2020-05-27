from imports import *

def validate_args(arguments):

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
