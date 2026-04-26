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
    default_mode: str | None


@dataclass(frozen=True)
class RemoteDefinition:
    name: str
    host: str
    user: str | None
    port: int | None
    identity_file: Path | None
    ssh_options: list[str]
    base_path: Path


@dataclass(frozen=True)
class RemoteJob:
    name: str
    sources: list[Path]
    remotes: list[str]
    rsync_flags: list[str]
    default_mode: str | None
    delete: bool | None


@dataclass(frozen=True)
class RemoteConfig:
    path: Path
    global_config: RemoteGlobalConfig
    remotes: dict[str, RemoteDefinition]
    jobs: list[RemoteJob]


class RemoteConfigLoader:
    def __init__(self, path: Path, logger: logging.Logger, cwd: Path | None = None):
        self.path = path.expanduser()
        self.logger = logger
        self.cwd = cwd or Path.cwd()

    def load(
        self,
        jobs_to_run: list[str] | None = None,
        require_jobs: bool = True,
    ) -> RemoteConfig:
        data = self._read()

        global_data = data.get("global", {})
        global_config = self._parse_global(global_data)

        remotes_data = data.get("remotes")
        if not isinstance(remotes_data, dict) or not remotes_data:
            raise SuisaveConfigError("Missing required [remotes.<label>] definitions.")
        remotes = self._parse_remotes(remotes_data)

        jobs_data = data.get("jobs", {})
        jobs = self._parse_jobs(jobs_data, global_config, remotes, jobs_to_run)

        if require_jobs and not jobs:
            raise SuisaveConfigError("No remote sync jobs were selected to run.")

        return RemoteConfig(
            path=self.path,
            global_config=global_config,
            remotes=remotes,
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

        default_mode = _validate_mode(data.get("default_mode"), "global config")

        return RemoteGlobalConfig(
            default_rsync_flags=list(flags),
            default_mode=default_mode,
        )

    def _parse_remotes(self, data: dict[str, Any]) -> dict[str, RemoteDefinition]:
        remotes: dict[str, RemoteDefinition] = {}
        for name, raw_remote in data.items():
            if not isinstance(raw_remote, dict):
                raise SuisaveConfigError(f"Invalid remote definition for {name!r}.")

            host = raw_remote.get("host")
            if host is None or host == "":
                raise SuisaveConfigError(f"Missing required host for remote {name!r}.")

            user = raw_remote.get("user")

            port = raw_remote.get("port")
            if port is not None and not isinstance(port, int):
                raise SuisaveConfigError(f"port must be an integer for remote {name!r}.")

            identity_file = raw_remote.get("identity_file")
            identity_path: Path | None = None
            if identity_file:
                identity_path = Path(identity_file).expanduser()
                if not identity_path.is_absolute():
                    identity_path = (self.path.parent / identity_path).resolve()

            ssh_options = raw_remote.get("ssh_options") or []
            if not isinstance(ssh_options, list):
                raise SuisaveConfigError(
                    f"ssh_options must be a list for remote {name!r}."
                )

            base_path = raw_remote.get("base_path")
            if base_path is None or base_path == "":
                raise SuisaveConfigError(
                    f"Missing required base_path for remote {name!r}."
                )

            remotes[name] = RemoteDefinition(
                name=name,
                host=host,
                user=user,
                port=port,
                identity_file=identity_path,
                ssh_options=list(ssh_options),
                base_path=Path(base_path),
            )

        return remotes

    def _parse_jobs(
        self,
        data: dict[str, Any],
        global_config: RemoteGlobalConfig,
        remotes: dict[str, RemoteDefinition],
        jobs_to_run: list[str] | None,
    ) -> list[RemoteJob]:
        sync_jobs = data.get("sync")
        if sync_jobs is None:
            return []
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

            remote_labels = _safe_list(
                raw_job,
                "remotes",
                f"There are no remotes for remote job: {name}",
            )
            remote_names = [str(label) for label in remote_labels]
            missing_remotes = [label for label in remote_names if label not in remotes]
            if missing_remotes:
                raise SuisaveConfigError(
                    f"Remote job {name!r} references unknown remotes: {missing_remotes}"
                )

            flags = raw_job.get("flags")
            if flags is None or not flags:
                flags = global_config.default_rsync_flags

            default_mode = raw_job.get("mode", raw_job.get("default_mode"))
            if default_mode is None:
                default_mode = global_config.default_mode
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
                    remotes=remote_names,
                    rsync_flags=list(flags),
                    default_mode=default_mode,
                    delete=delete,
                )
            )

        return final_jobs
