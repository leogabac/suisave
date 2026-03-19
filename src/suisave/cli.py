import sys
import suisave.cmds as cmd
from suisave.core import SuisaveError
from suisave.struct.logger import make_logger


VERSION = "0.3.0-alpha"


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
    # RUN COMMANDS
    # ================================

    run = sub.add_parser(
        "run",
        parents=[name_parent],
        help="Run jobs",
        description=("Run all rsync jobs from comet.toml configuration file."),
    )
    # ================================
    # CONFIG COMMANDS
    # ================================

    config = sub.add_parser(
        "config",
        parents=[name_parent],
        help="Config operations",
        description=("Commands for showing/maniputating comet.toml "),
    )
    config_sub = config.add_subparsers(
        dest="config_cmd",
        metavar="<config_command>",
        required=False,
    )

    # ===== DRIVE OPERATIONS ===== #
    config_drive = config_sub.add_parser(
        "drive",
        help="Drive configuration",
        description="Manage configured drives",
    )
    config_drive.add_argument(
        "--add",
        nargs=2,
        metavar=("LABEL", "UUID"),
        help="Add a new drive",
    )
    config_drive.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive mode",
    )

    config_drive.add_argument(
        "--remove",
        nargs=1,
        metavar=("LABEL",),
        help="Remove a drive by label",
    )

    # # ===== JOB OPERATIONS ===== #
    # config_job = config_sub.add_parser(
    #     "job",
    #     help="Job configuration",
    #     description="Manage configured drives",
    # )

    # ===== JOB OPERATIONS ===== #
    config_show = config_sub.add_parser(
        "show",
        help="Show config files",
        description="Show config file",
    )

    args = parser.parse_args()

    logger = make_logger()

    try:
        if args.cmd == "run":
            cmd.run_jobs(logger, jobs_to_run=args.name)
        elif args.cmd == "config":
            if args.config_cmd == "drive":
                cmd.config_drive_entry(logger, args)

            elif args.config_cmd == "job":
                raise SuisaveError("Unknown sub command.")

            elif args.config_cmd == "show":
                cmd.config_show(logger)

            else:
                raise SuisaveError("Unknown sub command.")

    except SuisaveError as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        exit(1)
    except KeyboardInterrupt:
        exit(0)


def desktop_entry():
    from pathlib import Path

    logger = make_logger()

    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    desktop_path = apps_dir / "suisave.desktop"

    content = f"""[Desktop Entry]
Version={VERSION}
Type=Application
Name=suisave
Comment=Simple Backups
Exec=bash -c "suisave run; exec bash"
Icon=drive-harddisk
Terminal=true
Categories=Utility;Application;
"""

    desktop_path.write_text(content, encoding="utf-8")

    logger.info("Desktop entry written to %s", desktop_path)
