from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import socket
import tempfile
from typing import Any

import tomlkit

from suisave.struct.comet import ensure_local_rsync_excludes


@dataclass
class EditableGlobal:
    pc_name: str = ""
    default_target_base: str = ""
    default_rsync_flags: list[str] = field(default_factory=list)


@dataclass
class EditableDrive:
    label: str
    uuid: str


@dataclass
class EditableJob:
    kind: str
    name: str
    sources: list[str] = field(default_factory=list)
    drives: list[str] = field(default_factory=list)
    target_base: str = ""
    flags: list[str] = field(default_factory=list)


@dataclass
class EditableConfig:
    global_config: EditableGlobal = field(default_factory=EditableGlobal)
    drives: list[EditableDrive] = field(default_factory=list)
    jobs: list[EditableJob] = field(default_factory=list)


def _default_pc_name() -> str:
    hostname = socket.gethostname()
    machine_id = Path("/etc/machine-id").read_text().strip()[:6]
    return f"{hostname}-{machine_id}"


def default_local_config() -> EditableConfig:
    return EditableConfig(
        global_config=EditableGlobal(
            pc_name="",
            default_target_base="",
            default_rsync_flags=[],
        ),
        drives=[],
        jobs=[],
    )


def load_local_config_model(path: Path) -> EditableConfig:
    if not path.exists():
        return default_local_config()

    with path.open("rb") as handle:
        data = tomlkit.load(handle)

    global_data = data.get("global", {})
    drives_data = data.get("drives", {})
    jobs_data = data.get("jobs", {})

    jobs: list[EditableJob] = []
    for kind in ("backup", "custom"):
        entries = jobs_data.get(kind, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            jobs.append(
                EditableJob(
                    kind=kind,
                    name=str(entry.get("name", "")),
                    sources=[str(item) for item in entry.get("sources", [])],
                    drives=[str(item) for item in entry.get("drives", [])],
                    target_base=str(entry.get("target_base", "")) if kind == "custom" else "",
                    flags=[str(item) for item in entry.get("flags", [])] if kind == "custom" else [],
                )
            )

    return EditableConfig(
        global_config=EditableGlobal(
            pc_name=str(global_data.get("pc_name", "")),
            default_target_base=str(global_data.get("default_target_base", "")),
            default_rsync_flags=[
                str(item) for item in global_data.get("default_rsync_flags", [])
            ],
        ),
        drives=[
            EditableDrive(label=str(label), uuid=str(value.get("uuid", "")))
            for label, value in drives_data.items()
            if isinstance(value, dict)
        ],
        jobs=jobs,
    )


def effective_global(global_config: EditableGlobal) -> EditableGlobal:
    pc_name = global_config.pc_name.strip() or _default_pc_name()
    default_target_base = global_config.default_target_base.strip() or "backups"
    flags = list(global_config.default_rsync_flags) or ["-avh", "--delete"]
    flags = ensure_local_rsync_excludes(flags)
    return EditableGlobal(
        pc_name=pc_name,
        default_target_base=default_target_base,
        default_rsync_flags=flags,
    )


def validate_local_config_model(config: EditableConfig) -> list[str]:
    problems: list[str] = []
    seen_drive_labels: set[str] = set()
    seen_job_names: set[str] = set()

    for drive in config.drives:
        label = drive.label.strip()
        uuid = drive.uuid.strip()
        if not label:
            problems.append("Drive labels cannot be empty.")
        elif label in seen_drive_labels:
            problems.append(f"Duplicate drive label: {label}")
        else:
            seen_drive_labels.add(label)
        if not uuid:
            problems.append(f"Drive {label or '<unnamed>'} is missing a UUID.")

    for index, job in enumerate(config.jobs, start=1):
        label = job.name.strip() or f"<unnamed job {index}>"
        if not job.name.strip():
            problems.append(f"Job {index} is missing a name.")
        elif job.name in seen_job_names:
            problems.append(f"Duplicate job name: {job.name}")
        else:
            seen_job_names.add(job.name)

        if not job.sources:
            problems.append(f"Job {label} must have at least one source.")
        if not job.drives:
            problems.append(f"Job {label} must reference at least one drive.")

        for source in job.sources:
            if not source.strip():
                problems.append(f"Job {label} contains an empty source entry.")

        for drive_label in job.drives:
            if drive_label not in seen_drive_labels:
                problems.append(
                    f"Job {label} references unknown drive label: {drive_label}"
                )

        if job.kind not in {"backup", "custom"}:
            problems.append(f"Job {label} has unsupported kind: {job.kind}")

    return problems


def dump_local_config_model(config: EditableConfig) -> str:
    doc = tomlkit.document()

    global_table = tomlkit.table()
    if config.global_config.pc_name.strip():
        global_table["pc_name"] = config.global_config.pc_name.strip()
    if config.global_config.default_target_base.strip():
        global_table["default_target_base"] = (
            config.global_config.default_target_base.strip()
        )
    if config.global_config.default_rsync_flags:
        global_table["default_rsync_flags"] = list(config.global_config.default_rsync_flags)
    if len(list(global_table.items())) > 0:
        doc["global"] = global_table
        doc.add(tomlkit.nl())

    drives_table = tomlkit.table()
    for drive in config.drives:
        entry = tomlkit.table()
        entry["uuid"] = drive.uuid.strip()
        drives_table[drive.label.strip()] = entry
    doc["drives"] = drives_table
    doc.add(tomlkit.nl())

    jobs_table = tomlkit.table()
    for kind in ("backup", "custom"):
        items = [job for job in config.jobs if job.kind == kind]
        if not items:
            continue
        array = tomlkit.aot()
        for job in items:
            entry = tomlkit.table()
            entry["name"] = job.name.strip()
            entry["sources"] = [item.strip() for item in job.sources if item.strip()]
            entry["drives"] = [item.strip() for item in job.drives if item.strip()]
            if kind == "custom":
                if job.target_base.strip():
                    entry["target_base"] = job.target_base.strip()
                if job.flags:
                    entry["flags"] = [item.strip() for item in job.flags if item.strip()]
            array.append(entry)
        jobs_table[kind] = array
    doc["jobs"] = jobs_table

    return tomlkit.dumps(doc, sort_keys=False)


def save_local_config_model(path: Path, config: EditableConfig) -> None:
    payload = dump_local_config_model(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def effective_job_target_base(config: EditableConfig, job: EditableJob) -> str:
    global_effective = effective_global(config.global_config)
    if job.kind == "backup":
        return str(Path(global_effective.default_target_base) / global_effective.pc_name)
    if job.target_base.strip():
        return job.target_base.strip()
    return global_effective.default_target_base


def effective_job_flags(config: EditableConfig, job: EditableJob) -> list[str]:
    global_effective = effective_global(config.global_config)
    if job.kind == "custom" and job.flags:
        return ensure_local_rsync_excludes(list(job.flags))
    return list(global_effective.default_rsync_flags)


def render_local_config_preview(config: EditableConfig) -> str:
    lines: list[str] = []
    problems = validate_local_config_model(config)
    effective = effective_global(config.global_config)

    if problems:
        lines.append("Validation")
        lines.append("")
        lines.extend(f"- {problem}" for problem in problems)
        lines.append("")
    else:
        lines.append("Validation")
        lines.append("")
        lines.append("- OK")
        lines.append("")

    lines.append("Effective Defaults")
    lines.append("")
    lines.append(f"- pc_name: {effective.pc_name}")
    lines.append(f"- default_target_base: {effective.default_target_base}")
    lines.append(
        f"- default_rsync_flags: {' '.join(effective.default_rsync_flags)}"
    )
    lines.append("")

    if config.jobs:
        lines.append("Job Preview")
        lines.append("")
        for job in config.jobs:
            target_base = effective_job_target_base(config, job)
            flags = " ".join(effective_job_flags(config, job))
            lines.append(f"- {job.kind}:{job.name or '<unnamed>'}")
            lines.append(f"  target base: {target_base}")
            lines.append(f"  flags: {flags}")
            if job.sources:
                for source in job.sources:
                    lines.append(f"  source: {source}")
            if job.drives:
                lines.append(f"  drives: {', '.join(job.drives)}")
        lines.append("")

    lines.append("TOML")
    lines.append("")
    lines.append(dump_local_config_model(config).rstrip())
    return "\n".join(lines)
