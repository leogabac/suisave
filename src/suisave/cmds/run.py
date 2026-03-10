from __future__ import annotations
from suisave.struct.comet import Comet
from suisave.struct.context import Job
from suisave.struct.stats import DirStats
from suisave.struct.logger import console
from suisave.core import CONFIG_PATH, run_rsync, notify
from pathlib import Path
from typing import List

from rich.table import Table


import threading

from dataclasses import dataclass, field


def monitor_progress(
    status,
    base_message: str,
    src_stats: DirStats,
    target: Path,
    job: Job,
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


def get_st_pairs(job):
    pairs: list[tuple[Path, Path]] = []

    for drive in job.drives:
        drive_dir = drive.mountpoint / job.tg_base

        for source in job.sources:
            target = drive_dir / source.relative_to(Path.home())
            target.mkdir(parents=True, exist_ok=True)
            pairs.append((source, target))

    return pairs


def run_single(logger, job: Job):
    logger.info("Starting job: %s", job.name)

    job_stats: List[str] = []
    pairs = get_st_pairs(job)

    base_status_message = f"[bold green]working on job [bold red]{job.name}"
    with console.status(base_status_message) as status:
        for source, target in pairs:
            logger.info("Working: %s -> %s", source, target)

            cmd = [
                "rsync",
                *job.rsync_flags,
                f"{source}/",
                f"{target}/",
            ]

            src_stats = DirStats(source, job)
            src_stats.compute()

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
                run_rsync(cmd, logger)
            finally:
                pass
                stop_event.set()
                monitor.join()

            # here i probably want to return the stats tuple object
            finish_stat = DirStats(source, job)
            finish_stat.compute()

            job_stats.append((src_stats, finish_stat))

    return job_stats


def run_jobs(logger, jobs_to_run: List[str] | None = None):
    comet = Comet(CONFIG_PATH, logger=logger)
    comet.load(jobs_to_run)

    all_stats: list[DirStats, DirStats] = []
    for job in comet.jobs:
        job_stats = run_single(logger, job)

        # i need to unwrap this
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

    notify("Backups Completed", "Press Enter in the Terminal to Exit", timeout=0)
    input("PRESS ENTER TO EXIT")
