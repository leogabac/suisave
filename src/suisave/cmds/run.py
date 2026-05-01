from __future__ import annotations

from pathlib import Path
from typing import List

from dataclasses import dataclass
import logging
import subprocess
import threading
import time

from rich.table import Table

from suisave.core import CONFIG_PATH, notify
from suisave.struct.comet import Comet
from suisave.struct.context import AbstractJob
from suisave.struct.logger import console
from suisave.struct.stats import DirStats
from suisave.ui.events import RunEvent
from suisave.ui.rich_run import run_with_rich_ui
from suisave.ui.textual_run import run_with_textual_ui


@dataclass
class PairResult:
    source_stats: DirStats
    target_stats: DirStats
    rsync_output: str


class LocalBackupRunner:
    def __init__(self, logger: logging.Logger, jobs: list[AbstractJob]):
        self.logger = logger
        self.jobs = jobs
        self.event_sink = lambda event: None

    def emit(self, kind: str, **payload) -> None:
        self.event_sink(RunEvent(kind=kind, payload=payload))

    def run(self) -> list[PairResult]:
        results: list[PairResult] = []
        total_pairs = sum(len(job.drives) * len(job.sources) for job in self.jobs)

        self.emit(
            "run_started",
            total_jobs=len(self.jobs),
            total_pairs=total_pairs,
        )

        global_pair_index = 0
        for job_index, job in enumerate(self.jobs, start=1):
            self.logger.debug("Starting job: %s", job.name)
            pairs = get_st_pairs(job)

            self.emit(
                "job_started",
                job_name=job.name,
                job_index=job_index,
                total_jobs=len(self.jobs),
                pair_count=len(pairs),
            )

            for pair_index, (source, target) in enumerate(pairs, start=1):
                global_pair_index += 1
                self.logger.debug("Working: %s -> %s", source, target)

                src_stats = DirStats(source, job)
                src_stats.compute()

                self.emit(
                    "pair_started",
                    job_name=job.name,
                    source=str(source),
                    target=str(target),
                    pair_index=pair_index,
                    pair_count=len(pairs),
                    global_pair_index=global_pair_index,
                    total_pairs=total_pairs,
                    source_size_human=src_stats.size_human,
                    source_files=src_stats.files,
                )

                try:
                    rsync_out = self._run_pair(job, source, target)
                except subprocess.CalledProcessError as exc:
                    self.emit(
                        "pair_failed",
                        job_name=job.name,
                        source=str(source),
                        target=str(target),
                        exit_code=exc.returncode,
                        output=exc.output or "",
                    )
                    raise

                finish_stat = DirStats(target, job)
                finish_stat.compute()
                result = PairResult(
                    source_stats=src_stats,
                    target_stats=finish_stat,
                    rsync_output=rsync_out,
                )
                results.append(result)

                self.emit(
                    "pair_finished",
                    job_name=job.name,
                    source=str(source),
                    target=str(target),
                    global_pair_index=global_pair_index,
                    total_pairs=total_pairs,
                    target_size_human=finish_stat.size_human,
                    target_files=finish_stat.files,
                )

            self.emit(
                "job_finished",
                job_name=job.name,
                job_index=job_index,
                total_jobs=len(self.jobs),
            )

        self.emit("run_finished")
        return results

    def _run_pair(self, job: AbstractJob, source: Path, target: Path) -> str:
        cmd = _build_rsync_cmd(job, source, target)
        stop_event = threading.Event()
        output_lines: list[str] = []

        monitor = threading.Thread(
            target=_monitor_target_snapshot,
            args=(self, job, target, stop_event),
            kwargs={"interval": 2.0},
            daemon=True,
        )
        monitor.start()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if process.stdout is None:
                raise RuntimeError("Failed to open rsync output stream.")

            reader = threading.Thread(
                target=_read_rsync_output,
                args=(self, process.stdout, output_lines),
                daemon=True,
            )
            reader.start()
            process.wait()
            reader.join()

            rsync_out = "".join(output_lines)
            if process.returncode != 0:
                self.logger.error("rsync failed with exit code %s", process.returncode)
                if rsync_out:
                    self.logger.error("rsync output:\n%s", rsync_out.strip())
                raise subprocess.CalledProcessError(
                    process.returncode,
                    cmd,
                    output=rsync_out,
                    stderr="",
                )

            return rsync_out
        finally:
            stop_event.set()
            monitor.join()


def _build_rsync_cmd(job: AbstractJob, source: Path, target: Path) -> list[str]:
    cmd = ["rsync", *job.rsync_flags]

    if "--outbuf=L" not in job.rsync_flags:
        cmd.append("--outbuf=L")
    if "--info=progress2" not in job.rsync_flags:
        cmd.append("--info=progress2")

    cmd.extend([f"{source}/", f"{target}/"])
    return cmd


def _read_rsync_output(
    runner: LocalBackupRunner,
    stream,
    output_lines: list[str],
) -> None:
    buffer = ""
    while True:
        chunk = stream.read(1)
        if chunk == "":
            break

        buffer += chunk
        if chunk not in {"\r", "\n"}:
            continue

        line = buffer.rstrip("\r\n")
        output_lines.append(buffer)
        _emit_rsync_line(runner, line)
        buffer = ""

    if buffer:
        output_lines.append(buffer)
        _emit_rsync_line(runner, buffer)


def _emit_rsync_line(runner: LocalBackupRunner, line: str) -> None:
    stripped = line.strip()
    if not stripped:
        return

    progress = parse_rsync_progress(stripped)
    if progress is not None:
        runner.emit("rsync_progress", **progress)
        return

    if stripped != "sending incremental file list":
        runner.emit("rsync_item", item=stripped)


def _monitor_target_snapshot(
    runner: LocalBackupRunner,
    job: AbstractJob,
    target: Path,
    stop_event: threading.Event,
    interval: float,
) -> None:
    while not stop_event.is_set():
        runner.emit("scan_started")
        try:
            stats = DirStats(target, job)
            stats.compute()
            runner.emit(
                "scan_completed",
                target_size_human=stats.size_human,
                target_files=stats.files,
            )
        except Exception as exc:
            runner.emit("scan_error", message=str(exc))

        if stop_event.wait(interval):
            break


def parse_rsync_progress(line: str) -> dict[str, str] | None:
    parts = line.split()
    if len(parts) < 4:
        return None

    bytes_done = parts[0].rstrip(",")
    percent = parts[1]
    rate = parts[2]
    eta = parts[3]
    if not percent.endswith("%") or "/s" not in rate:
        return None

    extra = " ".join(parts[4:]).strip()
    return {
        "bytes_done": bytes_done,
        "percent": percent.rstrip("%"),
        "rate": rate,
        "eta": eta,
        "extra": extra.strip("()") if extra else "",
    }


def get_st_pairs(job: AbstractJob) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []

    for drive in job.drives:
        drive_dir = drive.mountpoint / job.tg_base
        for source in job.sources:
            target = drive_dir / source.relative_to(Path.home())
            target.mkdir(parents=True, exist_ok=True)
            pairs.append((source, target))

    return pairs


def _print_summary(all_stats: list[PairResult]) -> None:
    table = Table(title="Summary")
    table.add_column("", justify="right")
    table.add_column("source", justify="left")
    table.add_column("target", justify="left")

    for result in all_stats:
        src = result.source_stats
        tg = result.target_stats
        table.add_row("name", src.name, tg.name)
        table.add_row("path", src.path._str, tg.path._str)
        table.add_row("size", src.size_human, tg.size_human)
        table.add_row("files", str(src.files), str(tg.files))
        table.add_section()

    console.print(table)


def run_jobs(
    logger: logging.Logger,
    jobs_to_run: List[str] | None = None,
    tui: bool = False,
):
    comet = Comet(CONFIG_PATH, logger=logger)
    comet.load(jobs_to_run)

    runner = LocalBackupRunner(logger, comet.jobs)
    results = run_with_textual_ui(runner) if tui else run_with_rich_ui(runner)

    _print_summary(results)
    notify("Backups Completed", "Check your terminal", timeout=5)
