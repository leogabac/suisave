from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Iterable

import argparse
import logging
import shlex

from rich.table import Table

from suisave.core import SuisaveConfigError, run_rsync
from suisave.struct.logger import console
from suisave.struct.remote import RemoteConfigLoader, RemoteConnection, RemoteJob


REMOTE_PUSH_MODES = {"push", "local"}
REMOTE_PULL_MODES = {"pull", "remote"}


def _build_ssh_transport(connection: RemoteConnection) -> str:
    cmd = ["ssh"]

    if connection.port is not None:
        cmd.extend(["-p", str(connection.port)])

    if connection.identity_file is not None:
        cmd.extend(["-i", str(connection.identity_file)])

    for option in connection.ssh_options:
        cmd.extend(["-o", option])

    return shlex.join(cmd)


def _format_remote_location(connection: RemoteConnection, remote_path: PurePosixPath) -> str:
    host = connection.host
    if connection.user:
        host = f"{connection.user}@{host}"

    return f"{host}:{shlex.quote(remote_path.as_posix())}"


def _source_suffix(source: Path, anchor: Path) -> PurePosixPath:
    try:
        relative_source = source.relative_to(anchor)
        if relative_source == Path("."):
            return PurePosixPath(anchor.name)
        return PurePosixPath(relative_source.as_posix())
    except ValueError:
        return PurePosixPath(source.name)


def _remote_target_for_source(job: RemoteJob, source: Path, anchor: Path) -> PurePosixPath:
    return PurePosixPath(job.target_base.as_posix()) / _source_suffix(source, anchor)


def _local_target_for_source(job: RemoteJob, source: Path, anchor: Path) -> Path:
    return anchor / Path(_remote_target_for_source(job, source, anchor))


def _apply_delete_override(flags: Iterable[str], delete: bool | None) -> list[str]:
    final_flags = [flag for flag in flags if flag != "--delete"]
    if delete is True:
        final_flags.append("--delete")
    return final_flags


def _resolve_mode(args: argparse.Namespace, job: RemoteJob, logger: logging.Logger) -> str:
    requested_modes = [
        ("push", bool(args.push)),
        ("pull", bool(args.pull)),
        ("most_recent", bool(args.most_recent)),
    ]
    enabled = [mode for mode, is_enabled in requested_modes if is_enabled]
    if len(enabled) > 1:
        raise SuisaveConfigError("Choose only one remote sync mode per invocation.")

    if enabled:
        mode = enabled[0]
    elif job.default_mode is not None:
        mode = job.default_mode
    else:
        raise SuisaveConfigError(
            f"Remote job {job.name!r} requires an explicit mode. "
            "Use --push or --pull, or configure default_mode."
        )

    if mode == "most_recent":
        raise SuisaveConfigError(
            "most_recent mode is not implemented yet. Use --push or --pull."
        )

    logger.info("Remote job %s will run in %s mode", job.name, mode)
    return mode


def _resolve_delete(job: RemoteJob, mode: str, cli_delete: bool | None) -> bool | None:
    if cli_delete is not None:
        return cli_delete
    if job.delete is not None:
        return job.delete
    if mode == "push":
        return True
    return None


def _build_push_cmd(
    connection: RemoteConnection,
    source: Path,
    remote_target: PurePosixPath,
    flags: list[str],
) -> list[str]:
    return [
        "rsync",
        *flags,
        "-e",
        _build_ssh_transport(connection),
        f"{source}/",
        _format_remote_location(connection, remote_target) + "/",
    ]


def _build_pull_cmd(
    connection: RemoteConnection,
    source: Path,
    local_target: Path,
    remote_target: PurePosixPath,
    flags: list[str],
) -> list[str]:
    local_target.parent.mkdir(parents=True, exist_ok=True)
    return [
        "rsync",
        *flags,
        "-e",
        _build_ssh_transport(connection),
        _format_remote_location(connection, remote_target) + "/",
        f"{local_target}/",
    ]


def _run_job(
    logger: logging.Logger,
    connection: RemoteConnection,
    job: RemoteJob,
    mode: str,
    cli_delete: bool | None,
    anchor: Path,
) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []

    delete = _resolve_delete(job, mode, cli_delete)
    flags = _apply_delete_override(job.rsync_flags, delete)

    for source in job.sources:
        remote_target = _remote_target_for_source(job, source, anchor)

        if mode in REMOTE_PUSH_MODES:
            cmd = _build_push_cmd(connection, source, remote_target, flags)
            destination = _format_remote_location(connection, remote_target)
            logger.info("Remote push: %s -> %s", source, destination)
            run_rsync(cmd, logger)
            rows.append((job.name, str(source), destination))
            continue

        if mode in REMOTE_PULL_MODES:
            local_target = _local_target_for_source(job, source, anchor)
            cmd = _build_pull_cmd(connection, source, local_target, remote_target, flags)
            origin = _format_remote_location(connection, remote_target)
            logger.info("Remote pull: %s -> %s", origin, local_target)
            run_rsync(cmd, logger)
            rows.append((job.name, origin, str(local_target)))
            continue

        raise SuisaveConfigError(f"Unsupported remote sync mode: {mode}")

    return rows


def _ad_hoc_job(
    remote_config,
    sources: list[str],
) -> RemoteJob:
    anchor = Path.cwd()
    resolved_sources: list[Path] = []
    missing: list[str] = []
    for raw_source in sources:
        source = Path(raw_source).expanduser()
        if not source.is_absolute():
            source = anchor / source
        source = source.resolve()
        if not source.exists():
            missing.append(str(source))
            continue
        resolved_sources.append(source)

    if missing:
        raise SuisaveConfigError(f"Ad hoc remote sources do not exist: {missing}")

    return RemoteJob(
        name="ad-hoc",
        sources=resolved_sources,
        target_base=remote_config.global_config.default_remote_base,
        rsync_flags=list(remote_config.global_config.default_rsync_flags),
        default_mode=remote_config.global_config.default_mode,
        delete=None,
    )


def remote_sync(logger: logging.Logger, args: argparse.Namespace) -> None:
    config_path = Path(args.config).expanduser()
    loader = RemoteConfigLoader(config_path, logger=logger, cwd=Path.cwd())
    remote_config = loader.load(args.name, require_jobs=not bool(args.source))

    jobs = remote_config.jobs
    if args.source:
        jobs = [_ad_hoc_job(remote_config, args.source)]

    cli_delete = None
    if args.delete:
        cli_delete = True
    elif args.no_delete:
        cli_delete = False

    results: list[tuple[str, str, str]] = []
    for job in jobs:
        mode = _resolve_mode(args, job, logger)
        rows = _run_job(
            logger,
            remote_config.connection,
            job,
            mode,
            cli_delete,
            Path.cwd(),
        )
        results.extend(rows)

    table = Table(title="Remote Sync Summary")
    table.add_column("job", justify="left")
    table.add_column("from", justify="left")
    table.add_column("to", justify="left")

    for job_name, origin, destination in results:
        table.add_row(job_name, origin, destination)

    console.print(table)
