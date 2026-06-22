from __future__ import annotations

import argparse
import logging
from pathlib import Path

import questionary
import tomlkit
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from suisave.core import CONFIG_PATH, SuisaveConfigError, SuisaveError, get_mountpoint
from suisave.core import get_mounted_devices
from suisave.struct.comet import Comet
from suisave.struct.context import BlockDevice


DEFAULT_CONFIG_TEMPLATE = """# Local suisave configuration
#
# See templates/comet.toml in the repository for a fuller commented example.

# [global]
# pc_name = "your_hostname"
# default_target_base = "backups"
# default_rsync_flags = ["-avh", "--delete", "--exclude=.venv/"]

[drives]
# [drives.main_backup]
# uuid = "XXXXXXXX-XXXX"

[jobs]
# [[jobs.backup]]
# name = "home"
# sources = ["/home/USERNAME"]
# drives = ["main_backup"]
"""


def config_entry(logger: logging.Logger, args: argparse.Namespace) -> None:
    if args.config_cmd == "path":
        config_path(logger)
        return

    if args.config_cmd == "init":
        config_init(logger, force=args.force)
        return

    if args.config_cmd == "show":
        config_show(logger)
        return

    if args.config_cmd == "drive":
        config_drive_entry(logger, args)
        return

    raise SuisaveError("Unknown config subcommand.")


def config_drive_entry(logger: logging.Logger, args: argparse.Namespace) -> None:
    if args.drive_cmd == "add":
        _drive_add(logger, name=args.label, uuid=args.uuid)
        return

    if args.drive_cmd == "rm":
        _drive_remove(logger, name=args.label)
        return

    if args.drive_cmd == "ls":
        config_drive_list(logger)
        return

    if args.drive_cmd == "detect":
        config_drive_detect(logger)
        return

    if args.drive_cmd == "select":
        _drive_select(logger)
        return

    raise SuisaveError("Unknown config drive subcommand.")


def _load_config_doc() -> tomlkit.TOMLDocument:
    if not CONFIG_PATH.exists():
        raise SuisaveConfigError(
            f"Config file not found: {CONFIG_PATH}. Run `suisave config init` first."
        )
    return tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))


def _write_config_doc(doc: tomlkit.TOMLDocument) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(tomlkit.dumps(doc, sort_keys=False), encoding="utf-8")


def config_path(logger: logging.Logger) -> None:
    logger.info("Config path: %s", CONFIG_PATH)


def config_init(logger: logging.Logger, force: bool = False) -> None:
    if CONFIG_PATH.exists() and not force:
        raise SuisaveConfigError(
            f"Config file already exists: {CONFIG_PATH}. Use `--force` to overwrite it."
        )

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    logger.info("Initialized config file at %s", CONFIG_PATH)


def _drive_add(logger: logging.Logger, name: str, uuid: str) -> None:
    logger.info("Opening config file...")
    doc = _load_config_doc()

    drives = doc.setdefault("drives", tomlkit.table())
    if name in drives:
        logger.warning("Drive '%s' already exists, overwriting", name)

    drive_entry = tomlkit.table()
    drive_entry["uuid"] = uuid
    drives[name] = drive_entry

    _write_config_doc(doc)
    logger.info("Added drive '%s'", name)


def _drive_remove(logger: logging.Logger, name: str) -> None:
    logger.info("Opening config file %s", CONFIG_PATH)
    doc = _load_config_doc()

    drives = doc.get("drives")
    if drives is None or name not in drives:
        raise SuisaveConfigError(f"Drive {name!r} not found in config.")

    del drives[name]
    if not drives:
        del doc["drives"]

    jobs = doc.get("jobs", {})
    removed_refs = 0

    for _, entries in jobs.items():
        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            job_drives = entry.get("drives")
            if not isinstance(job_drives, list):
                continue

            new_drives = [drive for drive in job_drives if drive != name]
            removed_refs += len(job_drives) - len(new_drives)
            entry["drives"] = new_drives

    _write_config_doc(doc)
    logger.info(
        "Removed drive '%s' from config and %d job reference(s)",
        name,
        removed_refs,
    )


def _drive_select(logger: logging.Logger) -> None:
    action = questionary.select(
        "What do you want to do?",
        choices=[
            Choice(title="Add drive", value="add"),
            Choice(title="Remove drive", value="remove"),
        ],
    ).ask()

    if action is None:
        return

    if action == "add":
        devices: list[BlockDevice] = []
        for data in get_mounted_devices():
            devices.append(
                BlockDevice(
                    name=data["name"],
                    uuid=data.get("uuid"),
                    mountpoint=Path(data["mountpoint"]),
                    label=data.get("label"),
                    fstype=data.get("fstype"),
                )
            )

        if not devices:
            raise SuisaveConfigError("No mounted block devices were detected.")

        idx = questionary.select(
            "Which device do you want to add?",
            choices=[
                Choice(
                    title=(
                        f"{device.name} / {device.label} / {device.mountpoint}"
                        f" / UUID {device.uuid}"
                    ),
                    value=i,
                )
                for i, device in enumerate(devices)
            ],
        ).ask()
        if idx is None:
            return

        selected_device = devices[idx]
        label = selected_device.label or selected_device.name
        if not selected_device.uuid:
            raise SuisaveConfigError(
                f"Selected device {selected_device.name!r} has no UUID."
            )
        _drive_add(logger, name=label, uuid=selected_device.uuid)
        return

    doc = _load_config_doc()
    drives = doc.get("drives", {})
    if not drives:
        raise SuisaveConfigError("No configured drives to remove.")

    drive_labels = list(drives.keys())
    idx = questionary.select(
        "Which configured drive do you want to remove?",
        choices=[
            Choice(
                title=f"{label} / UUID {drives[label].get('uuid', '')}",
                value=i,
            )
            for i, label in enumerate(drive_labels)
        ],
    ).ask()
    if idx is None:
        return

    _drive_remove(logger, drive_labels[idx])


def config_drive_detect(logger: logging.Logger) -> None:
    console = Console()
    devices = get_mounted_devices()

    table = Table(
        title="Mounted Devices",
        header_style="bold cyan",
        title_justify="left",
    )
    table.add_column("Name", style="green")
    table.add_column("Label", style="yellow")
    table.add_column("UUID", style="cyan")
    table.add_column("Mountpoint", style="magenta")
    table.add_column("FSType", style="white")

    if not devices:
        table.add_row("[dim]No mounted devices detected[/dim]", "", "", "", "")
    else:
        for device in devices:
            table.add_row(
                str(device.get("name", "")),
                str(device.get("label", "")),
                str(device.get("uuid", "")),
                str(device.get("mountpoint", "")),
                str(device.get("fstype", "")),
            )

    console.print(table)
    logger.info("Use `suisave config drive add LABEL UUID` to register a drive.")


def config_drive_list(logger: logging.Logger) -> None:
    console = Console()
    logger.info("Opening config file...")
    doc = _load_config_doc()

    drives = doc.get("drives", {})
    table = Table(
        title="Configured Drives",
        header_style="bold cyan",
        title_justify="left",
    )
    table.add_column("Label", style="green")
    table.add_column("UUID", style="yellow")
    table.add_column("Mounted", style="cyan")
    table.add_column("Mountpoint", style="magenta")

    if len(list(drives.items())) == 0:
        table.add_row("[dim]No drives configured[/dim]", "", "", "")
    else:
        for label, value in drives.items():
            uuid = value.get("uuid", "") if isinstance(value, dict) else str(value)
            mountpoint = get_mountpoint(uuid) if uuid else None
            mounted = "yes" if mountpoint is not None else "no"
            table.add_row(str(label), str(uuid), mounted, str(mountpoint or "-"))

    console.print(table)


def _show_global(console: Console, logger: logging.Logger, doc: tomlkit.TOMLDocument) -> None:
    parser = Comet(CONFIG_PATH, logger)
    global_config = parser._parse_global(doc.get("global", {}))

    table = Table(
        title="Global Defaults",
        header_style="bold blue",
        title_justify="left",
    )
    table.add_column("Field", style="green")
    table.add_column("Value", style="yellow")
    table.add_row("pc_name", global_config.pc_name)
    table.add_row("default_target_base", str(global_config.default_tg_base))
    table.add_row("default_rsync_flags", " ".join(global_config.default_rsync_flags))
    console.print(table)


def _show_drives(console: Console, doc: tomlkit.TOMLDocument) -> None:
    drives = doc.get("drives", {})

    table = Table(
        title="Configured Drives",
        header_style="bold cyan",
        title_justify="left",
    )
    table.add_column("Label", style="green")
    table.add_column("UUID", style="yellow")
    table.add_column("Mounted", style="cyan")
    table.add_column("Mountpoint", style="magenta")

    if len(list(drives.items())) == 0:
        table.add_row("[dim]No drives configured[/dim]", "", "", "")
    else:
        for label, value in drives.items():
            uuid = value.get("uuid", "") if isinstance(value, dict) else str(value)
            mountpoint = get_mountpoint(uuid) if uuid else None
            mounted = "yes" if mountpoint is not None else "no"
            table.add_row(str(label), str(uuid), mounted, str(mountpoint or "-"))

    console.print(table)


def _show_jobs(console: Console, logger: logging.Logger, doc: tomlkit.TOMLDocument) -> None:
    parser = Comet(CONFIG_PATH, logger)
    global_config = parser._parse_global(doc.get("global", {}))
    jobs = doc.get("jobs", {})

    if len(list(jobs.items())) == 0:
        console.print(
            Panel.fit(
                "[dim]No jobs configured[/dim]",
                title="Jobs",
                border_style="yellow",
            )
        )
        return

    for job_type, entries in jobs.items():
        table = Table(
            title=f"Jobs: {job_type}",
            header_style="bold magenta",
            title_justify="left",
        )
        table.add_column("Name", style="green")
        table.add_column("Sources", style="yellow")
        table.add_column("Drives", style="cyan")
        table.add_column("Effective target base", style="magenta")
        table.add_column("Flags", style="white")

        if not isinstance(entries, list) or not entries:
            table.add_row("[dim]No entries[/dim]", "", "", "", "")
            console.print(table)
            continue

        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                table.add_row(f"invalid-{index}", "[red]Invalid job entry[/red]", "", "", "")
                continue

            name = entry.get("name", f"unnamed-{index}")
            sources = entry.get("sources", [])
            drives = entry.get("drives", [])

            if job_type == "backup":
                target_base = global_config.default_tg_base / global_config.pc_name
                flags = global_config.default_rsync_flags
            else:
                target_base = Path(
                    entry.get("target_base", global_config.default_tg_base)
                )
                flags = entry.get("flags", global_config.default_rsync_flags)

            table.add_row(
                str(name),
                ", ".join(str(source) for source in sources) or "-",
                ", ".join(str(drive) for drive in drives) or "-",
                str(target_base),
                " ".join(str(flag) for flag in flags) or "-",
            )

        console.print(table)


def config_show(logger: logging.Logger) -> None:
    console = Console()
    logger.info("Opening config file...")
    doc = _load_config_doc()

    console.print(
        Panel.fit(
            f"[bold]suisave config[/bold]\n[dim]{CONFIG_PATH}[/dim]",
            title="Configuration",
        )
    )

    _show_global(console, logger, doc)
    _show_drives(console, doc)
    _show_jobs(console, logger, doc)
