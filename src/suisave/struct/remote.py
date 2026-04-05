from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import logging
import tomllib

from suisave.core import SuisaveConfigError


VALID_REMOTE_MODES = {"push", "pull", "most_recent"}


def _safe_string(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return value


def _safe_list(data: dict[str, Any], key: str, message: str) -> list[Any]:
    value = data.get(key)
    if value is None or not isinstance(value, list) or not value:
        raise SuisaveConfigError(message)
    return value


def _validate_mode(mode: str | None, context: str) -> str | None:
    if mode is None:
        return None
    if mode not in VALID_REMOTE_MODES:
        raise SuisaveConfigError(
            f"Invalid remote sync mode for {context}: {mode!r}. "
            f"Expected one of {sorted(VALID_REMOTE_MODES)}."
        )
    return mode


def _resolve_existing_sources(
    sources: list[str],
    cwd: Path,
    job_name: str,
    logger: logging.Logger,
) -> list[Path]:
    resolved: list[Path] = []
    missing: list[str] = []

    for raw_source in sources:
        source = Path(raw_source).expanduser()
        if not source.is_absolute():
            source = cwd / source
        source = source.resolve()

        if not source.exists():
            missing.append(str(source))
            continue

        logger.debug("found remote source %s for job %s", source, job_name)
        resolved.append(source)

    if missing:
        raise SuisaveConfigError(
            f"Sources {missing} do not exist for remote job {job_name!r}."
        )

    return resolved


@dataclass(frozen=True)
class RemoteGlobalConfig:
    default_rsync_flags: list[str]
    default_remote_base: Path
    default_mode: str | None


@dataclass(frozen=True)
class RemoteConnection:
    host: str
    user: str | None
    port: int | None
    identity_file: Path | None
    ssh_options: list[str]


@dataclass(frozen=True)
class RemoteJob:
    name: str
    sources: list[Path]
    target_base: Path
    rsync_flags: list[str]
    default_mode: str | None
    delete: bool | None


@dataclass(frozen=True)
class RemoteConfig:
    path: Path
    global_config: RemoteGlobalConfig
    connection: RemoteConnection
    jobs: list[RemoteJob]


class RemoteConfigLoader:
    def __init__(self, path: Path, logger: logging.Logger, cwd: Path | None = None):
        self.path = path.expanduser()
        self.logger = logger
        self.cwd = cwd or Path.cwd()

    def load(self, jobs_to_run: list[str] | None = None) -> RemoteConfig:
        data = self._read()

        global_data = data.get("global", {})
        global_config = self._parse_global(global_data)

        connection_data = data.get("connection")
        if not isinstance(connection_data, dict):
            raise SuisaveConfigError("Missing required [connection] table.")
        connection = self._parse_connection(connection_data)

        jobs_data = data.get("jobs", {})
        jobs = self._parse_jobs(jobs_data, global_config, jobs_to_run)

        if not jobs:
            raise SuisaveConfigError("No remote sync jobs were selected to run.")

        return RemoteConfig(
            path=self.path,
            global_config=global_config,
            connection=connection,
            jobs=jobs,
        )

    def _read(self) -> dict[str, Any]:
        try:
            with self.path.open("rb") as handle:
                return tomllib.load(handle)
        except FileNotFoundError as exc:
            raise SuisaveConfigError(f"Config file not found: {self.path}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise SuisaveConfigError(f"TOML parse error: {exc}") from exc

    def _parse_global(self, data: dict[str, Any]) -> RemoteGlobalConfig:
        flags = data.get("default_rsync_flags")
        if flags is None or flags == "" or not flags:
            flags = ["-azvh"]

        remote_base = data.get("default_remote_base")
        if remote_base is None or remote_base == "":
            remote_base_path = Path(".")
        else:
            remote_base_path = Path(remote_base)

        default_mode = _validate_mode(data.get("default_mode"), "global config")

        return RemoteGlobalConfig(
            default_rsync_flags=list(flags),
            default_remote_base=remote_base_path,
            default_mode=default_mode,
        )

    def _parse_connection(self, data: dict[str, Any]) -> RemoteConnection:
        host = data.get("host")
        if host is None or host == "":
            raise SuisaveConfigError("Missing required connection.host value.")

        user = data.get("user")

        port = data.get("port")
        if port is not None and not isinstance(port, int):
            raise SuisaveConfigError("connection.port must be an integer.")

        identity_file = data.get("identity_file")
        identity_path: Path | None = None
        if identity_file:
            identity_path = Path(identity_file).expanduser()
            if not identity_path.is_absolute():
                identity_path = (self.path.parent / identity_path).resolve()

        ssh_options = data.get("ssh_options") or []
        if not isinstance(ssh_options, list):
            raise SuisaveConfigError("connection.ssh_options must be a list.")

        return RemoteConnection(
            host=host,
            user=user,
            port=port,
            identity_file=identity_path,
            ssh_options=list(ssh_options),
        )

    def _parse_jobs(
        self,
        data: dict[str, Any],
        global_config: RemoteGlobalConfig,
        jobs_to_run: list[str] | None,
    ) -> list[RemoteJob]:
        sync_jobs = data.get("sync")
        if not isinstance(sync_jobs, list) or not sync_jobs:
            raise SuisaveConfigError("No [[jobs.sync]] entries found in remote config.")

        final_jobs: list[RemoteJob] = []
        for index, raw_job in enumerate(sync_jobs):
            if not isinstance(raw_job, dict):
                raise SuisaveConfigError("Invalid [[jobs.sync]] entry.")

            name = _safe_string(raw_job.get("name"), f"unnamed-{index}")
            if jobs_to_run is not None and name not in jobs_to_run:
                self.logger.debug(
                    "skipping remote job %s as per user's instruction", name
                )
                continue

            raw_sources = _safe_list(
                raw_job,
                "sources",
                f"There are no sources for remote job: {name}",
            )
            sources = _resolve_existing_sources(
                [str(source) for source in raw_sources],
                self.cwd,
                name,
                self.logger,
            )

            target_base = raw_job.get("target_base")
            if target_base is None or target_base == "":
                target_base_path = global_config.default_remote_base
            else:
                target_base_path = Path(target_base)

            flags = raw_job.get("flags")
            if flags is None or not flags:
                flags = global_config.default_rsync_flags

            default_mode = raw_job.get("default_mode", global_config.default_mode)
            default_mode = _validate_mode(default_mode, f"job {name!r}")

            delete = raw_job.get("delete")
            if delete is not None and not isinstance(delete, bool):
                raise SuisaveConfigError(
                    f"delete must be a boolean when set for remote job {name!r}."
                )

            final_jobs.append(
                RemoteJob(
                    name=name,
                    sources=sources,
                    target_base=target_base_path,
                    rsync_flags=list(flags),
                    default_mode=default_mode,
                    delete=delete,
                )
            )

        return final_jobs
