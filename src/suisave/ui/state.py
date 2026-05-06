from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time

from suisave.ui.events import RunEvent


def format_elapsed(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


@dataclass
class RunState:
    started_at: float | None = None
    finished_at: float | None = None
    total_jobs: int = 0
    total_pairs: int = 0
    completed_jobs: int = 0
    completed_pairs: int = 0
    current_job: str = "-"
    current_source: str = "-"
    current_target: str = "-"
    current_pair_index: int = 0
    current_pair_count: int = 0
    source_size_human: str = "-"
    source_files: int = 0
    target_size_human: str = "0.00 B"
    target_files: int = 0
    scan_started_at: float | None = None
    last_scan_finished_at: float | None = None
    last_scan_error: str | None = None
    rsync_bytes: str | None = None
    rsync_percent: str | None = None
    rsync_rate: str | None = None
    rsync_eta: str | None = None
    rsync_extra: str | None = None
    current_item: str | None = None
    last_progress_at: float | None = None
    recent_events: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    failed: bool = False
    failure_exit_code: str | None = None
    failure_output: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def handle(self, event: RunEvent) -> None:
        with self.lock:
            match event.kind:
                case "run_started":
                    self.started_at = event.timestamp
                    self.total_jobs = int(event.payload["total_jobs"])
                    self.total_pairs = int(event.payload["total_pairs"])
                    self._push(
                        f"run started: {self.total_jobs} jobs, {self.total_pairs} source/target pairs"
                    )
                case "job_started":
                    self.current_job = str(event.payload["job_name"])
                    self.current_pair_count = int(event.payload["pair_count"])
                    self._push(f"job started: {self.current_job}")
                case "pair_started":
                    self.current_source = str(event.payload["source"])
                    self.current_target = str(event.payload["target"])
                    self.current_pair_index = int(event.payload["pair_index"])
                    self.current_pair_count = int(event.payload["pair_count"])
                    self.source_size_human = str(event.payload["source_size_human"])
                    self.source_files = int(event.payload["source_files"])
                    self.target_size_human = "0.00 B"
                    self.target_files = 0
                    self.current_item = None
                    self.rsync_bytes = None
                    self.rsync_percent = None
                    self.rsync_rate = None
                    self.rsync_eta = None
                    self.rsync_extra = None
                    self.scan_started_at = None
                    self.last_scan_finished_at = None
                    self.last_scan_error = None
                    self.last_progress_at = event.timestamp
                    self._push(
                        f"pair started: {self.current_source} -> {self.current_target}"
                    )
                case "rsync_progress":
                    self.rsync_bytes = str(event.payload["bytes_done"])
                    self.rsync_percent = str(event.payload["percent"])
                    self.rsync_rate = str(event.payload["rate"])
                    self.rsync_eta = str(event.payload["eta"])
                    self.rsync_extra = str(event.payload["extra"])
                    self.last_progress_at = event.timestamp
                case "rsync_item":
                    self.current_item = str(event.payload["item"])
                    self.last_progress_at = event.timestamp
                case "scan_started":
                    self.scan_started_at = event.timestamp
                    self.last_scan_error = None
                case "scan_completed":
                    self.target_size_human = str(event.payload["target_size_human"])
                    self.target_files = int(event.payload["target_files"])
                    self.last_scan_finished_at = event.timestamp
                    self.scan_started_at = None
                case "scan_error":
                    self.last_scan_error = str(event.payload["message"])
                    self.last_scan_finished_at = event.timestamp
                    self.scan_started_at = None
                    self._push(f"monitor warning: {self.last_scan_error}")
                case "pair_finished":
                    self.completed_pairs = int(event.payload["global_pair_index"])
                    self.target_size_human = str(event.payload["target_size_human"])
                    self.target_files = int(event.payload["target_files"])
                    self._push(
                        f"pair finished: {event.payload['source']} -> {event.payload['target']}"
                    )
                case "job_finished":
                    self.completed_jobs = int(event.payload["job_index"])
                    self._push(f"job finished: {event.payload['job_name']}")
                case "pair_failed":
                    msg = (
                        f"pair failed with exit code {event.payload['exit_code']}: "
                        f"{event.payload['source']} -> {event.payload['target']}"
                    )
                    self.failed = True
                    self.failure_exit_code = str(event.payload["exit_code"])
                    self.failure_output = str(event.payload.get("output") or "").strip()
                    self.finished_at = event.timestamp
                    self.errors.append(msg)
                    self._push(msg)
                    if self.failure_output:
                        self._push(self.failure_output.splitlines()[-1])
                case "run_finished":
                    self.finished_at = event.timestamp
                    self._push("run finished")

    def _push(self, message: str) -> None:
        self.recent_events.append(message)
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)

    def snapshot(self) -> dict[str, str]:
        with self.lock:
            now = time.monotonic()
            elapsed = format_elapsed(
                (self.finished_at or now) - self.started_at
            ) if self.started_at is not None else "00:00"

            if self.scan_started_at is not None:
                scan_status = (
                    "scanning target "
                    f"({format_elapsed(now - self.scan_started_at)})"
                )
            elif self.last_scan_finished_at is not None:
                scan_status = (
                    "last scan "
                    f"{format_elapsed(now - self.last_scan_finished_at)} ago"
                )
            else:
                scan_status = "waiting for first scan"

            if self.last_scan_error:
                scan_status = f"{scan_status} | warning: {self.last_scan_error}"

            activity = "rsync active"
            heartbeat = "receiving live progress"
            if self.last_progress_at is not None:
                idle_for = now - self.last_progress_at
                if idle_for >= 15:
                    heartbeat = "no new rsync output; large file, delete, or metadata work possible"
                if idle_for >= 60:
                    activity = "rsync process still running; progress updates sparse"
                if idle_for >= 180:
                    heartbeat = "no new rsync or scan signal for a while; target may be very slow"

            progress_line = "waiting for rsync progress"
            if self.rsync_percent is not None:
                progress_line = (
                    f"{self.rsync_bytes} | {self.rsync_percent}% | "
                    f"{self.rsync_rate} | eta {self.rsync_eta}"
                )
                if self.rsync_extra:
                    progress_line += f" | {self.rsync_extra}"

            return {
                "elapsed": elapsed,
                "jobs": f"{self.completed_jobs}/{self.total_jobs}",
                "pairs": f"{self.completed_pairs}/{self.total_pairs}",
                "current_job": self.current_job,
                "current_pair": f"{self.current_pair_index}/{self.current_pair_count}",
                "source": self.current_source,
                "target": self.current_target,
                "source_snapshot": f"{self.source_size_human} | {self.source_files} files",
                "target_snapshot": f"{self.target_size_human} | {self.target_files} files",
                "progress_line": progress_line,
                "rsync_bytes": self.rsync_bytes or "-",
                "rsync_percent": self.rsync_percent or "0",
                "rsync_rate": self.rsync_rate or "-",
                "rsync_eta": self.rsync_eta or "-",
                "rsync_extra": self.rsync_extra or "-",
                "current_item": self.current_item or "-",
                "scan_status": scan_status,
                "activity": activity,
                "heartbeat": heartbeat,
                "events": "\n".join(self.recent_events) if self.recent_events else "No events yet.",
                "errors": "\n".join(self.errors) if self.errors else "No errors.",
                "failed": "yes" if self.failed else "no",
                "failure_exit_code": self.failure_exit_code or "-",
                "failure_output": self.failure_output or "",
                "finished": "yes" if self.finished_at is not None else "no",
            }
