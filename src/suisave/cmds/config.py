import logging
import argparse
import tomlkit

from suisave.core import SuisaveError, CONFIG_PATH, get_mounted_devices
from suisave.struct.context import BlockDevice

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary
from questionary import Choice


def config_drive_entry(logger: logging.Logger, args: argparse.Namespace) -> None:
    """
    Entrypoint for operations on DRIVES in the config file
    """

    if args.add is not None:
        logger.debug("drive add mode")
        _drive_add(
            logger,
            name=args.add[0],
            uuid=args.add[1],
        )

    elif args.remove is not None:
        logger.debug("drive add mode")
        _drive_remove(
            logger,
            name=args.remove[0],
        )

    elif args.interactive:
        logger.debug("drive interactive mode")
        _drive_interactive(logger)

    else:
        raise SuisaveError("Unknown flag/command. Get some help.")


def _drive_add(logger: logging.Logger, name: str, uuid: str):
    """
    Add a drive to the config file based on its label and UUID
    """
    logger.info("Opening config file...")

    doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))

    drives = doc.setdefault("drives", tomlkit.table())

    if name in drives:
        logger.warning("Drive '%s' already exists, overwriting", name)

    drive_entry = tomlkit.table()
    drive_entry["uuid"] = uuid

    drives[name] = drive_entry
    doc["drives"][name] = drive_entry
    doc.add(tomlkit.nl())

    CONFIG_PATH.write_text(tomlkit.dumps(doc, sort_keys=False), encoding="utf-8")

    logger.info("Added drive '%s'", name)


def _drive_remove(logger: logging.Logger, name: str):
    """
    Remove the drive from the configuration file.
    Additionally walk through every job and remove all leftover drive references.
    """
    logger.info(f"Opening config file {CONFIG_PATH._str}")

    doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))

    drives = doc.get("drives")
    if drives is None or name not in drives:
        logger.error("Drive '%s' not found", name)
        return

    # Remove from top-level drives section
    del drives[name]
    if not drives:
        del doc["drives"]

    # Remove from every job entry
    jobs = doc.get("jobs", {})
    removed_refs = 0

    for job_name, entries in jobs.items():
        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            job_drives = entry.get("drives")
            if not isinstance(job_drives, list):
                continue

            new_drives = [d for d in job_drives if d != name]
            removed_refs += len(job_drives) - len(new_drives)
            entry["drives"] = new_drives

    CONFIG_PATH.write_text(tomlkit.dumps(doc), encoding="utf-8")

    logger.info(
        "Removed drive '%s' from config and %d job reference(s)",
        name,
        removed_refs,
    )


def _drive_interactive(logger: logging.Logger):
    """
    Launch an interactive mode for drive add/remove operations.
    Powered by the questionary library.
    """

    action = questionary.select(
        "What do you want to do?",
        choices=[
            "add drive",
            "remove drive",
        ],
    ).ask()

    if action == "add drive":

        devices: list[BlockDevice] = []
        for d in get_mounted_devices():
            blkdev = BlockDevice(
                name=d["name"],
                uuid=d.get("uuid"),
                mountpoint=d["mountpoint"],
                label=d.get("label"),
                fstype=d.get("fstype"),
            )

            devices.append(blkdev)

        options = [
            f"{blkdev.name} / {blkdev.label} with UUID {blkdev.uuid}"
            for blkdev in devices
        ]

        idx = questionary.select(
            "Which device to add?",
            choices=[Choice(title=opt, value=i) for i, opt in enumerate(options)],
        ).ask()
        selected_device = devices[idx]
        _drive_add(logger, name=selected_device.label, uuid=selected_device.uuid)

    else:
        doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))
        drives: dict = doc.get("drives")
        drive_labels: list[str] = []
        display_options: list[str] = []
        for drive_label, val in drives.items():
            drive_labels.append(drive_label)
            uuid = val.get("uuid", None)
            display_options.append(f"{drive_label} with UUID {uuid}")

        idx = questionary.select(
            "Which device to remove?",
            choices=[
                Choice(title=opt, value=i) for i, opt in enumerate(display_options)
            ],
        ).ask()
        selected_label = drive_labels[idx]
        _drive_remove(logger, selected_label)


def config_show(logger: logging.Logger):
    console = Console()

    logger.info("Opening config file...")

    if not CONFIG_PATH.exists():
        console.print(f"[bold red]Config file not found:[/bold red] {CONFIG_PATH}")
        return

    doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))

    console.print(
        Panel.fit(
            f"[bold]suisave config[/bold]\n[dim]{CONFIG_PATH}[/dim]",
            title="Configuration",
        )
    )

    # =========================
    # Drives
    # =========================
    drives_table = Table(
        title="Drives",
        header_style="bold cyan",
        title_justify="left",
    )
    drives_table.add_column("Label", style="green")
    drives_table.add_column("UUID", style="yellow")

    drives = doc.get("drives", {})

    if drives:
        for label, value in drives.items():
            uuid = value.get("uuid", "") if isinstance(value, dict) else value
            drives_table.add_row(str(label), str(uuid))
    else:
        drives_table.add_row("[dim]No drives configured[/dim]", "")

    console.print(drives_table)

    # =========================
    # Jobs
    # =========================
    jobs = doc.get("jobs", {})

    if not jobs:
        console.print(
            Panel.fit(
                "[dim]No jobs configured[/dim]", title="Jobs", border_style="yellow"
            )
        )
        return

    for job_name, entries in jobs.items():
        job_table = Table(
            title=f"Job: {job_name}",
            header_style="bold magenta",
            title_justify="left",
        )

        job_table.add_column("#", justify="right")
        job_table.add_column("Source", style="green")
        job_table.add_column("Target base", style="cyan")
        job_table.add_column("Drives", style="yellow")

        row_id = 1

        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                sources = entry.get("sources", [])
                tg_base = str(entry.get("tg_base", ""))
                job_drives = entry.get("drives", [])

                # normalize drives display
                if isinstance(job_drives, list):
                    drives_str = ", ".join(str(x) for x in job_drives)
                else:
                    drives_str = str(job_drives)

                # 👇 key change: iterate sources
                for src in sources:
                    job_table.add_row(
                        str(row_id),
                        str(src),
                        tg_base,
                        drives_str,
                    )
                    row_id += 1
        else:
            job_table.add_row("-", "[red]Invalid job format[/red]", "", "")

        if row_id == 1:
            job_table.add_row("-", "[dim]No sources[/dim]", "", "")

        console.print(job_table)
