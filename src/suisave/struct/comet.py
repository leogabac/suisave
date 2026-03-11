from __future__ import annotations

from pathlib import Path
from typing import Any, List, Dict

import tomllib  # Python 3.11+
import socket
import logging

from suisave.struct.context import (
    GlobalConfig,
    Drive,
    AbstractJob,
    BackupJob,
    CustomJob,
)
from suisave.core import (
    SuisaveConfigError,
    SuisaveDriveError,
    get_mountpoint,
)


def safe_string(text, replace):
    """
    Quickly replace a text if I got None or an empty string.
    """
    if (text is None) or (text == ""):
        text = replace
    return text


def safe_get_list(data: dict, key: str, msg, error=SuisaveConfigError):
    """
    Quickly verify the integrity of a list from the data dictionary
    """
    drives: List[str] = data.get(key, None)
    if (drives is None) or (not drives):
        raise error(msg)

    return drives


def check_sources(
    sources: List[Path], job_name: str, logger: logging.Logger
) -> List[Path]:
    """
    From a list of sources, check whether they exist or not.
    If something does not exist, it exits cleanly.
    """
    bad_sources: List[str] = []
    good_sources: List[Path] = []
    for i, s in enumerate(sources):
        s = Path(s)
        if not s.exists():
            bad_sources.append(s._str)
        else:
            logger.debug(f"found source {s._str} for job {job_name}")
            good_sources.append(s)

    if bad_sources:
        raise SuisaveConfigError(f"Sources {bad_sources} do not exist! Exiting")

    return good_sources


def get_valid_drives(
    drives_in_config: List[Drive],
    drives_in_job: List[str],
    job_name: str,
    logger: logging.Logger,
):
    todo_drives: List[Drive] = []
    todo_drives_name: List[str] = []
    # get the drives that are mounted and parsed correctly
    for conf_drive in drives_in_config:
        if conf_drive.name in drives_in_job:
            todo_drives.append(conf_drive)
            todo_drives_name.append(conf_drive.name)

    # directly exit if nothing is found
    if not todo_drives:
        raise SuisaveDriveError(
            f"None of the required drives for job {job_name} were mounted! Exiting."
        )

    # get the drives that are supposed to use, but are not mounted
    for job_drive in drives_in_job:
        if job_drive not in todo_drives_name:
            logger.warning(
                f"Job {job_name} requires drive {job_name} but it is not mounted. Skipping."
            )

    return todo_drives


class Comet:
    def __init__(self, path: Path, logger: logging.Logger):
        self.path = path
        self.logger = logger

        self.global_config: GlobalConfig = None
        self.drives: List[Drive] = None
        self.jobs: List[AbstractJob] = None

    def load(self, jobs_to_run: list[str]) -> None:
        """
        Parse the configuration file according to the jobs that
        are actually going to be run.

        Initializes instance fields.

        Parameters:
        ----------
        * jobs_to_run: list[str]

        Returns:
        ----------
        * None
        """
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
        """
        Read the TOML file from the config directory.

        Returns:
        ----------
        * config_dict: Dict[str, Any]
        """
        try:
            with self.path.open("rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            raise SuisaveConfigError(f"Config file not found: {self.path}")
        except tomllib.TOMLDecodeError as e:
            raise SuisaveConfigError(f"TOML parse error: {e}") from e

    def _parse_global(self, data: Dict[str, Any]):
        """
        Parse the configuration file according to the jobs that
        are actually going to be run.

        Initializes instance fields.

        Parameters:
        ----------
        * jobs_to_run: list[str]

        Returns:
        ----------
        * None
        """
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
            uuid = value.get("uuid", None)
            if uuid is None or uuid == "":
                raise SuisaveDriveError(
                    f"Not a valid UUID for drive f{name}, got {uuid=}."
                )
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
        data: Dict[str, Any],
        jobs_to_run: List[str],
    ) -> List[AbstractJob]:
        final_jobs: List[AbstractJob] = []

        # first go through all of the types of backups
        for jobtype, jobdata in data.items():
            # and first compute some of the shared logic that they have
            for i, raw_job in enumerate(jobdata):
                # determine and error handle the job name
                name = safe_string(raw_job.get("name", None), f"unnamed-{i}")

                if (jobs_to_run is not None) and (name not in jobs_to_run):
                    self.logger.debug(f"skipping job {name} as per user's instruction")
                    continue

                # get my source dirs and check for the integrity of all of them
                sources: List[str] = safe_get_list(
                    raw_job, "sources", msg=f"There are no sources for job: {name}"
                )
                good_src = check_sources(sources, name, self.logger)

                # get the drives i wanna work with
                drives_in_job: List[str] = safe_get_list(
                    raw_job, "drives", msg=f"There are no drives for job: {name}"
                )

                todo_drives = get_valid_drives(
                    self.drives, drives_in_job, name, self.logger
                )

                # here there is no elegant way other than just go one by one
                if jobtype == "backup":
                    final_jobs.append(
                        BackupJob(
                            name,
                            good_src,
                            todo_drives,
                            global_config=self.global_config,
                        )
                    )

                elif jobtype == "custom":
                    # finally, the rsync flags
                    flags: List[str] = raw_job.get("flags", None)
                    if (flags is None) or (not flags):
                        flags = self.global_config.default_rsync_flags

                    tg_base: Path = raw_job.get("target_base", None)
                    if tg_base is None:
                        tg_base = self.global_config.default_tg_base
                    tg_base = Path(tg_base)

                    final_jobs.append(
                        CustomJob(
                            name,
                            good_src,
                            todo_drives,
                            tg_base=tg_base,
                            rsync_flags=flags,
                        )
                    )

        return final_jobs
