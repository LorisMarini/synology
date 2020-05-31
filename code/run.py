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

    # Get user input
    stage_opts = ["y", "n"]
    stage_question = (f"\nDo you want to stage files? {'/'.join(stage_opts)}: ")
    stage_answer = cli_ask_question(question=stage_question, options=stage_opts)

    if stage_answer == "y":

        validate_staging(args)

        # Prepare migration from dump
        plan_staging = plan(source=args.dump, destinations=args.staging, ignore=args.ignore)

        # Execute migration
        execute(df=plan_staging, mode=args.mode, replace=args.replace)

        # Prepare migration to server from staging
        plan_server = plan(source=args.staging["HOME"], destinations=args.server, ignore=args.ignore)

    else:
        # Prepare direct migration to server
        plan_server = plan(source=args.dump, destinations=args.server, ignore=args.ignore)

    # Confirm load job
    load_options = ["y", "n"]
    load_question = (f"\nReady to load data to the server? {'/'.join(load_options)}: ")
    load_answer = cli_ask_question(question=load_question, options=load_options)

    if load_answer == "y":
        # Execute migration
        execute(df=plan_server, mode=args.mode, replace=args.replace)
    else:
        print(f"\nAll files are ready to load in staging. Abortng.")
        return

    if stage_answer == "y":
        # Cleanup
        optionally_clean_dir(args.staging["HOME"])

if __name__ == "__main__":
    main()
