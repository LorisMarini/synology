#!/Users/lorismarini/anaconda3/bin/python

"""
This solves the problem of organizing content automatically
based on the date of creation, as well as loading it to the
server while keeping track of any errors thet might arise.
"""

from imports import *
from validate import *
from helpers import *
from plan import *
from execute import *


def default_staging_paths():

    staging_home = '/Volumes/loris/VideoStaging'

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
    return ['.jsonl', '.json', '.aae']


@dataclass(init=True, repr=True)
class Arguments:
    # Dump directory
    # dump: str = field(default ='/Users/lorismarini/ds918/dump')
    dump: str = field(default ="/Volumes/loris/VideoDump")
    # Staging directories
    staging: dict = field(default_factory = default_staging_paths)
    # server directories
    server: dict = field(default_factory = default_server_paths)
    # Any file extensions to ignore
    ignore: list = field(default_factory = default_ignore)
    # If existing files are found
    replace: bool = False
    # Migration mode
    mode: str = 'move'


def main() -> None:

    # Instantiate default args object
    args = Arguments()

    # Validate and assign args to a global variable
    validate_args(args)

    staging_home = args.staging["HOME"]

    print(f"\nMigration settings:"
          f"\n  dump: {args.dump}"
          f"\n  staging_home: {args.staging['HOME']}"
          f"\n  server_home: {args.server['HOME']}"
          f"\n  replace: {args.replace}"
          f"\n  mode: {args.mode}")

    # Get user input
    options = ["y", "n"]
    question = (f"\nDo you want to stage files fist? {'/'.join(options)}: ")
    stage_data = cli_ask_question(question=question, options=options)

    if stage_data == "y":

        validate_staging(args)

        # Prepare migration
        p = plan(source=args.dump, destinations=args.staging, ignore=args.ignore)
        # Execute migration
        execute(df=p, mode=args.mode, replace=args.replace)

        # Confirm load job
        o = ["y", "n"]
        q = (f"\nReady to load data to the server? {'/'.join(o)}: ")
        a = cli_ask_question(question=q, options=o)
        if a == "y":
            # Prepare migration
            p = plan(source=staging_home, destinations=args.server, ignore=args.ignore)
            # Execute migration
            execute(df=p, mode=args.mode, replace=args.replace)

            # Cleanup
            options = ["y", "n"]
            question = (f"\nDo you want to clean {staging_home}? {'/'.join(options)}: ")
            clean = cli_ask_question(question=question, options=options)
            if clean == "y":
                clean_directory(staging_home)
        else:
            print(f"\nAll files are ready to load in {staging_home}. Abortng.")
            return

    else:
        # Prepare migration
        p = plan(source=args.dump, destinations=args.server, ignore=args.ignore)

        # Save plan to file for inspection
        timenow = pd.Timestamp.now()
        timestring = timenow.strftime("%Y%m%d_%H%M%S_%f")
        saveas = f"./.plans/{timestring}_server_plan.csv"
        p.to_csv(saveas)

        # Confirm load job
        o = ["y", "n"]
        q = (f"\nPlan saved at {saveas}. \nReady to load data to the server? {'/'.join(o)}: ")
        a = cli_ask_question(question=q, options=o)
        if a == "y":
            # Execute migration
            execute(df=p, mode=args.mode, replace=args.replace)
        else:
            print(f"\nAbortng.")
            return



if __name__ == "__main__":
    main()
