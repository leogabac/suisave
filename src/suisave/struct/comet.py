from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Dict

import tomllib  # Python 3.11+
import socket
import logging

from suisave.struct.context import Config, GlobalConfig, Drive, Job
from suisave.core import SuisaveConfigError, SuisaveDriveError, get_mountpoint
import warnings


class Comet:
    def __init__(self, path: Path, logger: logging.Logger):
        self.path = path
        self.logger = logger

        self.global_config: GlobalConfig = None
        self.drives: List[Drive] = None
        self.jobs: List[Job] = None

    def load(self, jobs_to_run) -> Config:
        toml_file = self._read()

        # parse the global options and return a config object
        global_data = toml_file.get("global", None)
        if global_data is None:
            global_data = dict()
        self.global_config = self._parse_global(global_data)

        drives_data = toml_file.get("drives", None)
        if not drives_data:
            raise SuisaveConfigError("Drive table is empty! Try setting up a drive.")

        self.drives = self._parse_drives(drives_data)

        jobs_data = toml_file["jobs"]
        self.jobs = self._parse_jobs(jobs_data, jobs_to_run)

    def _read(self) -> Dict[str, Any]:
        try:
            with self.path.open("rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            raise SuisaveConfigError(f"Config file not found: {self.path}")
        except tomllib.TOMLDecodeError as e:
            raise SuisaveConfigError(f"TOML parse error: {e}") from e

    def _parse_global(self, data: Dict[str, Any]) -> GlobalConfig:
        pc_name = data.get("pc_name", None)
        if pc_name is None or pc_name == "":
            hostname = socket.gethostname()
            machine_id = Path("/etc/machine-id").read_text().strip()[:6]
            pc_name = f"{hostname}-{machine_id}"

        tg_base = data.get("default_target_base", None)
        if tg_base is None or tg_base == "":
            tg_base = Path("backups")
        else:
            tg_base = Path(tg_base)

        rsync_flags = data.get("default_rsync_flags", None)
        if (rsync_flags is None) or (rsync_flags == "") or (not rsync_flags):
            rsync_flags = ["-avh", "--delete"]

        self.logger.debug("loaded global options file")

        return GlobalConfig(
            pc_name=pc_name,
            default_tg_base=tg_base,
            default_rsync_flags=rsync_flags,
        )

    def _parse_drives(self, data: dict[str, Any]) -> Dict[str, Drive]:
        drives = []
        for name, value in data.items():
            uuid = value["uuid"]
            mountpoint = get_mountpoint(uuid)
            if mountpoint is None:
                self.logger.warning(f"Drive {name} with {uuid} is not mounted.")
                continue

            self.logger.debug(f"found drive {name} with {uuid} at {mountpoint}")
            drives.append(Drive(name, uuid, mountpoint))

        self.logger.debug("loaded drive information")
        return drives

    def _parse_jobs(
        self,
        data: List[dict],
        jobs_to_run: List[str],
    ) -> List[Job]:
        final_jobs: List[Job] = []

        for i, raw_job in enumerate(data):
            # determine and error handle the job name
            name = raw_job.get("name", None)
            if (name is None) or (name == ""):
                name = f"unnamed-{i}"

            if (jobs_to_run is not None) and (name not in jobs_to_run):
                self.logger.debug(f"skipping job {name} as per user's instruction")
                continue

            # determine and error handle sources
            # additionally determine if the sources exist or not
            sources = raw_job.get("sources", None)
            if (sources is None) or (not sources):
                raise SuisaveConfigError(f"There are no sources for job: {name}")

            bad_sources: List[str] = []
            good_sources: List[Path] = []
            for i, s in enumerate(sources):
                s = Path(s)
                if not s.exists():
                    bad_sources.append(s._str)
                else:
                    self.logger.debug(f"found source {s._str} for job {name}")
                    good_sources.append(s)

            if bad_sources:
                raise SuisaveConfigError(f"Sources {bad_sources} do not exist! Exiting")

            # get the drives i wanna work with
            drives: List[str] = raw_job.get("drives", None)
            if (drives is None) or (not drives):
                raise SuisaveConfigError(f"There are no drives for job: {name}")

            todo_drives: List[Drive] = []
            todo_drives_name: List[str] = []
            # get the drives that are mounted and parsed correctly
            for drive in self.drives:
                if drive.name in drives:
                    todo_drives.append(drive)
                    todo_drives_name.append(drive.name)

            # directly exit if nothing is found
            if not todo_drives:
                raise SuisaveDriveError(
                    f"None of the required drives for job {name} were mounted! Exiting."
                )

            # get the drives that are supposed to use, but are not mounted
            for drive in drives:
                if not (drive in todo_drives_name):
                    self.logger.warning(
                        f"Job {name} requires drive {drive} but it is not mounted. Skipping."
                    )

            # finally, the rsync flags
            flags: List[str] = raw_job.get("flags", None)
            if (flags is None) or (not flags):
                flags = self.global_config.default_rsync_flags

            tg_base: Path = raw_job.get("target_base", None)
            if tg_base is None:
                tg_base = self.global_config.default_tg_base
            tg_base = Path(tg_base)

            pc_name: str = raw_job.get("pc_name", None)
            if pc_name is None:
                pc_name = self.global_config.pc_name
            pc_name = Path(pc_name)

            tg_base = tg_base / pc_name

            final_jobs.append(Job(name, good_sources, todo_drives, tg_base, flags))
        self.logger.debug("loaded jobs information")
        return final_jobs
