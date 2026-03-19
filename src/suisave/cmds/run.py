from __future__ import annotations
from suisave.struct.comet import Comet
from suisave.struct.context import AbstractJob
from suisave.struct.stats import DirStats
from suisave.struct.logger import console
from suisave.core import CONFIG_PATH, LOGS_PATH, run_rsync, notify
from pathlib import Path
from typing import List, Any

from datetime import datetime
import time

import logging

from rich.table import Table

import threading


def monitor_progress(
    status,
    base_message: str,
    src_stats: DirStats,
    target: Path,
    job: AbstractJob,
    stop_event: threading.Event,
    interval: float = 0.5,
) -> None:
    """
    Periodically print comparison between source and current target state
    while rsync is running.
    """

    while not stop_event.is_set():
        try:
            # text = src_stats.compare_with(target, skip_header=False)
            tg_stat = DirStats(target, job)
            tg_stat.compute()

            msg = [
                base_message,
                f"{tg_stat.size_human}/{src_stats.size_human} | {tg_stat.files}/{src_stats.files} files",
            ]
            status.update(" | ".join(msg))
        except Exception as e:
            print(f"[monitor error] {e}", flush=True)

        # Wait with stop awareness
        if stop_event.wait(interval):
            break


def get_st_pairs(job: AbstractJob) -> tuple[Path, Path]:
    """
    Make a list of tuples containing
    (source_dir, target_dir)
    """
    pairs: list[tuple[Path, Path]] = []

    for drive in job.drives:
        drive_dir = drive.mountpoint / job.tg_base

        for source in job.sources:
            target = drive_dir / source.relative_to(Path.home())
            target.mkdir(parents=True, exist_ok=True)
            pairs.append((source, target))

    return pairs


def run_single(logger: logging.Logger, job: AbstractJob) -> tuple[str, List[Any]]:
    """
    Run a rsync on a single job.

    Parameters:
    ----------
    * logger: Logger object from python's module
    * job: Job to run

    Returns:
    ----------
    * job_stats: List[tuple[DirStats, DirStats]]
        List containing a tuple with DirStats of source and target after
        the job is finished.
    """

    logger.info("Starting job: %s", job.name)

    job_stats: List[tuple[DirStats, DirStats]] = []  # initialize
    pairs: List[tuple[Path, Path]] = get_st_pairs(job)

    base_status_message = f"[bold green]working on job [bold red]{job.name}"
    # here the basic idea is to open the status message
    # then go one by one in src-target executing and updating the status window

    with console.status(base_status_message) as status:
        for source, target in pairs:
            logger.info("Working: %s -> %s", source, target)

            cmd = [
                "rsync",
                *job.rsync_flags,
                f"{source}/",
                f"{target}/",
            ]

            # i can precompute the src_stats once at the beginning to avoid doing it multple times
            src_stats = DirStats(source, job)
            src_stats.compute()

            # threading black sorcery
            # the basic idea is to execute the monitor_progress() function while rsync is running
            stop_event = threading.Event()
            monitor = threading.Thread(
                target=monitor_progress,
                args=(
                    status,
                    base_status_message + "[bold white]",
                    src_stats,
                    target,
                    job,
                    stop_event,
                ),
                kwargs={"interval": 0.1},
                daemon=True,
            )

            monitor.start()
            try:
                rsync_out = run_rsync(cmd, logger)
            finally:
                stop_event.set()
                monitor.join()

            # here i probably want to return the stats tuple object
            finish_stat = DirStats(target, job)
            finish_stat.compute()

            job_stats.append((src_stats, finish_stat))

    return rsync_out, job_stats


def run_jobs(logger: logging.Logger, jobs_to_run: List[str] | None = None):
    """
    Run all required jobs, defaults to all.

    Parameters:
    ----------
    * logger
    * jobs_to_run: List[str]
        List of job names to run
    """
    # timestamp = time.time()
    # formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y%m%d-%H%M%S")
    #
    # log_dir = LOGS_PATH / formatted_time
    # n_logs = len(list(log_dir.parent.iterdir()))
    #
    # if n_logs >= 5:
    #     logger.warning(f"There are {n_logs} saved logs. Consider a cleanup.")
    # Path.mkdir(log_dir, parents=True, exist_ok=True)
    # logger.info(f"Saving rsync outs to: {log_dir}")
    #
    comet = Comet(CONFIG_PATH, logger=logger)
    comet.load(jobs_to_run)

    all_stats: list[DirStats, DirStats] = []
    for job in comet.jobs:
        rsync_out, job_stats = run_single(logger, job)

        # the job stat is a fancy list that if i append naively
        # it will make a mess of list of lists, thus i will first make a quick unwrap here
        # to append globally for printing later
        for stat in job_stats:
            all_stats.append(stat)

    # make a cool table for display
    table = Table(title="Summary")
    table.add_column("", justify="right")
    table.add_column("source", justify="left")
    table.add_column("target", justify="left")
    for src, tg in all_stats:
        table.add_row("name", src.name, tg.name)
        table.add_row("path", src.path._str, tg.path._str)
        table.add_row("size", src.size_human, tg.size_human)
        table.add_row("files", str(src.files), str(tg.files))
        table.add_section()
    console.print(table)

    notify("Backups Completed", "Check your terminal", timeout=5)

    base_status_message = "Backups Completed."
    with console.status(base_status_message) as status:
        for i in reversed(range(30)):
            msg = f"{base_status_message} Terminal will close in {i} seconds... or press Ctrl+c"
            status.update(msg)
            time.sleep(1)
