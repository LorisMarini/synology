from imports import *

if __name__ == "__main__":

    USAGE = """
    This solves the problem of organizing content automatically
    based on the date of creation, as well as loading it to the
    server while keeping track of any errors thet might arise.

    Example 1:
        python run.py -r "True" -m "copy" --dump "~/dump" --staging "~/stg" --server "~/server"
    """

    mode_help = "Mode help."

    # Get the description from the docstring of the function
    parser = argparse.ArgumentParser(usage=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)

    # Set values of default arguments
    parser.set_defaults(dump="",
                        staging={},
                        server={},
                        ignore=[],
                        replace=False,
                        mode="copy")

    parser.add_argument('-d', '--dump', type=str, required=False, help=mode_help)
    parser.add_argument('--staging', type=str, required=False, help=mode_help)
    parser.add_argument('--server', type=str, required=False, help=mode_help)
    parser.add_argument('-i', '--ignore', type=list, required=False, help=mode_help)
    parser.add_argument('-r', '--replace', type=bool, required=False, help=mode_help)
    parser.add_argument('-m', '--mode', type=str, required=False, help=mode_help)

    # Parse parameters
    args = parser.parse_args()

    # call the function that writes json activity data to an HDF5 store
    args = {'dump': args.dump,
            'staging': args.staging,
            'server': args.server,
            'ignore': args.ignore,
            'replace': args.replace,
            'mode': args.mode}

    print(args)
