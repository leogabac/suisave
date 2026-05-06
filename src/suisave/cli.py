import sys
import suisave.cmds as cmd
from suisave.core import SuisaveError, SuisaveRunCancelled
from suisave.struct.logger import make_logger


VERSION = "0.3.1-alpha"


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
    run.add_argument(
        "--no-interactive",
        action="store_true",
        help="Use the non-TUI terminal dashboard and print the shell summary table.",
    )

    remote = sub.add_parser(
        "remote",
        help="Remote sync operations",
        description=("Commands for syncing project-local directories to remote hosts."),
    )
    remote_sub = remote.add_subparsers(
        dest="remote_cmd",
        metavar="<remote_command>",
        required=True,
    )

    remote_sync = remote_sub.add_parser(
        "sync",
        parents=[name_parent],
        help="Run remote sync jobs",
        description=("Run remote rsync jobs from a local TOML config file."),
    )
    remote_sync.add_argument(
        "--config",
        required=True,
        help="Path to the remote TOML config file.",
    )
    remote_sync.add_argument(
        "--source",
        nargs="+",
        metavar="path",
        help="Run an ad hoc sync for one or more local sources.",
    )
    remote_sync.add_argument(
        "--target",
        nargs="+",
        metavar="label",
        help="Limit the run to one or more named remote targets from the config.",
    )
    remote_mode = remote_sync.add_mutually_exclusive_group(required=False)
    remote_mode.add_argument(
        "--push",
        "--local",
        dest="push",
        action="store_true",
        help="Treat local files as the source of truth and send them to the remote.",
    )
    remote_mode.add_argument(
        "--pull",
        "--remote",
        dest="pull",
        action="store_true",
        help="Treat the remote files as the source of truth and pull them locally.",
    )
    remote_mode.add_argument(
        "--most-recent",
        action="store_true",
        help="Choose sync direction from the most recently modified side.",
    )
    remote_delete = remote_sync.add_mutually_exclusive_group(required=False)
    remote_delete.add_argument(
        "--delete",
        action="store_true",
        help="Delete files on the destination that no longer exist on the source side.",
    )
    remote_delete.add_argument(
        "--no-delete",
        action="store_true",
        help="Do not delete files on the destination side.",
    )
    # ================================
    # CONFIG COMMANDS
    # ================================

    config = sub.add_parser(
        "config",
        help="Local config operations",
        description="Inspect and manage ~/.config/suisave/comet.toml.",
    )
    config_sub = config.add_subparsers(
        dest="config_cmd",
        metavar="<config_command>",
        required=True,
    )

    config_sub.add_parser(
        "path",
        help="Print the local config path",
        description="Show the path to ~/.config/suisave/comet.toml.",
    )

    config_init = config_sub.add_parser(
        "init",
        help="Create a starter local config file",
        description="Create ~/.config/suisave/comet.toml with a starter template.",
    )
    config_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the existing config file if it already exists.",
    )

    config_sub.add_parser(
        "show",
        help="Show the effective local config",
        description="Show parsed local config values, drive status, and jobs.",
    )

    config_drive = config_sub.add_parser(
        "drive",
        help="Manage configured drives",
        description="Add, remove, inspect, and detect local backup drives.",
    )
    config_drive_sub = config_drive.add_subparsers(
        dest="drive_cmd",
        metavar="<drive_command>",
        required=True,
    )

    config_drive_add = config_drive_sub.add_parser(
        "add",
        help="Add or update a drive registration",
        description="Register a drive label and UUID in the local config.",
    )
    config_drive_add.add_argument("label", help="Drive label in the config.")
    config_drive_add.add_argument("uuid", help="Filesystem UUID for the drive.")

    config_drive_rm = config_drive_sub.add_parser(
        "rm",
        help="Remove a configured drive",
        description="Remove a drive registration and any job references to it.",
    )
    config_drive_rm.add_argument("label", help="Drive label to remove.")

    config_drive_sub.add_parser(
        "ls",
        help="List configured drives",
        description="Show configured drives and whether they are currently mounted.",
    )
    config_drive_sub.add_parser(
        "detect",
        help="List mounted block devices",
        description="Show mounted devices detected from lsblk.",
    )
    config_drive_sub.add_parser(
        "select",
        help="Interactively add or remove a drive",
        description="Launch an interactive selector for drive add/remove operations.",
    )

    args = parser.parse_args()

    logger = make_logger()

    try:
        if args.cmd == "run":
            cmd.run_jobs(
                logger,
                jobs_to_run=args.name,
                interactive=not args.no_interactive,
            )
        elif args.cmd == "remote":
            if args.remote_cmd == "sync":
                cmd.remote_sync(logger, args)
            else:
                raise SuisaveError("Unknown sub command.")
        elif args.cmd == "config":
            cmd.config_entry(logger, args)

    except SuisaveRunCancelled:
        exit(0)
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
Exec=suisave run; exec bash
Icon=drive-harddisk
Terminal=true
Categories=Utility;Application;
"""

    desktop_path.write_text(content, encoding="utf-8")

    logger.info("Desktop entry written to %s", desktop_path)
