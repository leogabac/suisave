from suisave.struct.comet import Comet
from suisave.struct.context import Job
from suisave.core import CONFIG_PATH, notify, run_rsync
from pathlib import Path
from typing import List
import asyncio
from desktop_notifier import DesktopNotifier
import time


def run_single(job: Job):
    pass


def run_jobs(logger, jobs_to_run: List[str] | None = None):
    comet = Comet(CONFIG_PATH, logger=logger)
    comet.load(jobs_to_run)

    for job in comet.jobs:
        logger.info("Starting job: %s", job.name)

        pairs: list[tuple[Path, Path]] = []

        for drive in job.drives:
            drive_dir = drive.mountpoint / job.tg_base

            for source in job.sources:
                target = drive_dir / source.relative_to(Path.home())
                target.mkdir(parents=True, exist_ok=True)
                pairs.append((source, target))

        for source, target in pairs:
            logger.info("Working: %s -> %s", source, target)
            cmd = [
                "rsync",
                *job.rsync_flags,
                f"{source}/",
                f"{target}/",
            ]

            run_rsync(cmd, logger)

            # result = run_rsync(
            #     source=source,
            #     target=target,
            #     rsync_flags=job.rsync_flags,
            #     logger=logger,
            # )
            #
    # return summary
    notify("Backups Completed", "Press Enter in the Terminal to Exit", timeout=0)
    input("PRESS ENTER TO EXIT")
