import sys
import logging
import suisave.cmds as cmd
from suisave.core import SuisaveError
from suisave.struct.logger import get_logger, make_logger, PanelLogHandler


VERSION = "0.3.0-pre"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="suisave",
        description=("A simple, text-configured backup tool.\n\n"),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    sub = parser.add_subparsers(
        dest="cmd",
        metavar="<command>",
    )

    # ================================
    # Shared parent arguments
    # ================================
    name_parent = argparse.ArgumentParser(add_help=False)
    name_parent.add_argument(
        "--name",
        "-n",
        metavar="str",
        nargs="+",
        help=("Name of backup to run.\nDefaults to all."),
    )

    # ================================
    # CONFIG COMMANDS
    # ================================
    run = sub.add_parser(
        "run",
        parents=[name_parent],
        help="Run backup jobs",
        description=(
            "Commands for creating, inspecting, and launching tmux sessions "
            "from grem.yaml configuration files."
        ),
    )

    args = parser.parse_args()

    # logger = get_logger(name="suisave", level=logging.INFO)
    logger = make_logger()

    if args.cmd == "run":
        try:
            cmd.run_jobs(logger, jobs_to_run=args.name)
        except SuisaveError as e:
            # print(f"{e.__class__.__name__}: {e}")
            print(f"{type(e).__name__}: {e}", file=sys.stderr)
            exit(1)


def config():
    print("hello 2")
