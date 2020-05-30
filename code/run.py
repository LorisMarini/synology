#!/Users/lorismarini/anaconda3/bin/python

USAGE = """
This solves the problem of organizing content automatically
based on the date of creation, as well as loading it to the
server while keeping track of any errors thet might arise.

Example 1:
    python run.py -r "True" -m "copy" -i "['.jsonl', '.json', '.aae']" --dump "~/dump" --staging "~/stg" --server "~/server"
"""

from imports import *
from helpers import *
from plan import *
from execute import *

code = pathlib.Path(__file__).parent.absolute()
data = code.parent / "data"


def optionally_clean_dir(directory):
    # Cleanup
    options = ["y", "n"]
    question = (f"\nDo you want to clean {directory}? {'/'.join(options)}: ")
    clean = cli_ask_question(question=question, options=options)
    if clean == "y":
        clean_directory(directory)
    return


def main() -> None:

    mode_help = "Mode help."

    # Get the description from the docstring of the function
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     usage=USAGE)

    # Set values of default arguments
    parser.set_defaults(dump="",
                        staging=str(data / "staging"),
                        server=str(data / "server"),
                        ignore=['.jsonl', '.json', '.aae'],
                        replace=False,
                        mode="copy")

    parser.add_argument('-d', '--dump', type=str, required=False, help=mode_help)
    parser.add_argument('--staging', type=str, required=False, help=mode_help)
    parser.add_argument('--server', type=str, required=False, help=mode_help)
    parser.add_argument('-i', '--ignore', type=list, required=False, help=mode_help)
    parser.add_argument('-r', '--replace', type=bool, required=False, help=mode_help)
    parser.add_argument('-m', '--mode', type=str, required=False, help=mode_help)

    # Parse parameters
    cli_args = parser.parse_args()

    # Instantiate default args object
    args = Arguments(cli_args.dump,
                    staging_paths(cli_args.staging),
                    server_paths(cli_args.server),
                    cli_args.ignore,
                    cli_args.replace,
                    cli_args.mode)
    print(args)

    staging_home = args.staging["HOME"]

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
            optionally_clean_dir(staging_home)

        else:
            print(f"\nAll files are ready to load in {staging_home}. Abortng.")
            return

    else:
        # Prepare migration
        p = plan(source=args.dump, destinations=args.server, ignore=args.ignore)

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
