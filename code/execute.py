from imports import *
from helpers import *

# Get the directory of this file
here = pathlib.Path(__file__).parent.absolute()
# FInd plans directory
plans_dir = here.parent / "_plans"


def execute(*, df:pd.DataFrame, mode:str, replace:str):

    print(f"\nExecuting...")

    # Create destination directories if they don't exist
    dst_dirs = df["abspath_dst"].apply(lambda x: os.path.dirname(x))
    dst_dirs_unique = dst_dirs.unique()
    _ = [os.makedirs(d, exist_ok=True) for d in dst_dirs_unique]

    reports = []
    # tqdm wraps the iterable and roduces a progress bar
    for i in tqdm(df.index):

        # Get src and dst directories
        src = df.loc[i,"abspath_src"]
        dst = df.loc[i,"abspath_dst"]

        # Migrate file
        report = migrate_file(src=src, dst=dst, mode=mode, replace=replace)
        reports.append(report)

    # Build a table of migrations
    report_table = pd.DataFrame(reports)
    copied = report_table["copied"].sum()
    moved = report_table["moved"].sum()
    skipped = report_table["skipped"].sum()
    error = report_table["error"].count()

    print(f"\n - copied {copied}"
          f"\n - moved {moved}"
          f"\n - skipped {skipped}"
          f"\n - errors {error}")

    # Save plan to file for inspection
    timestring = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S_%f")
    saveas = plans_dir / f"{timestring}_migration_report.csv"
    report_table.to_csv(saveas)

    print(f"\nReport ready ({os.path.basename(saveas)})")
    print(f"Preview:\n")
    print(tabulate(report_table.head(), headers=list(report_table.columns)))


def migrate_file(*, src:str, dst:str, mode:str, replace:bool) -> dict:

    report = {"src": os.path.basename(src),
              "dst": os.path.basename(dst),
              "copied": False,
              "moved": False,
              "skipped": False,
              "error": None}

    try:
        if not os.path.exists(src):
            message = f"DATA INTEGRITY: File {src} expected but not found. Skipping"
            raise ValueError(message)

        if os.path.exists(dst) and not replace:
            # If it already exists and we don't want to relace skip
            report["skipped"] = True
        else:
            # File in src exists
            if mode =="copy":
                # copy file preserving metadata
                # https://docs.python.org/3/library/shutil.html#shutil.copy2
                shutil.copy2(src, dst)
                report["copied"] = True
            elif mode =="move":
                # Move file preserving metadata
                # https://docs.python.org/3/library/shutil.html#shutil.move
                shutil.move(src, dst, copy_function=shutil.copy2)
                report["moved"] = True
            else:
                message = f"Migration mode {args.mode} not supported."
                raise ValueError(message)

    except Exception as ex:
        report["error"] = str(ex)
    return report
