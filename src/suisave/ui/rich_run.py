from __future__ import annotations

from queue import Empty, Queue
import threading
import time

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from suisave.ui.state import RunState


def _run_runner(runner, event_queue: Queue, result_box: dict[str, object]) -> None:
    runner.event_sink = event_queue.put
    try:
        result_box["result"] = runner.run()
    except Exception as exc:
        result_box["error"] = exc


def _render_dashboard(state: RunState):
    data = state.snapshot()

    overview = Table.grid(expand=True)
    overview.add_column(ratio=1)
    overview.add_column(ratio=3)
    overview.add_row("Elapsed", data["elapsed"])
    overview.add_row("Jobs", data["jobs"])
    overview.add_row("Pairs", data["pairs"])
    overview.add_row("Job", data["current_job"])
    overview.add_row("Pair", data["current_pair"])
    overview.add_row("Source", data["source"])
    overview.add_row("Target", data["target"])

    percent = float(data["progress_line"].split("|")[1].strip().rstrip("%")) if "%" in data["progress_line"] else 0.0
    progress_group = Group(
        Text(data["activity"]),
        ProgressBar(total=100, completed=percent),
        Text(f"rsync {data['progress_line']}"),
        Text(f"item {data['current_item']}"),
        Text(f"source snapshot {data['source_snapshot']}"),
        Text(f"target snapshot {data['target_snapshot']}"),
        Text(data["scan_status"]),
    )

    return Group(
        Panel(overview, title="Run"),
        Panel(progress_group, title="Transfer"),
        Panel(data["events"], title="Events"),
    )


def run_with_rich_ui(runner):
    event_queue: Queue = Queue()
    state = RunState()
    result_box: dict[str, object] = {}
    worker = threading.Thread(
        target=_run_runner,
        args=(runner, event_queue, result_box),
        daemon=True,
    )
    worker.start()

    with Live(_render_dashboard(state), refresh_per_second=8) as live:
        while worker.is_alive() or not event_queue.empty():
            drained = False
            while True:
                try:
                    event = event_queue.get_nowait()
                except Empty:
                    break
                state.handle(event)
                drained = True

            if drained:
                live.update(_render_dashboard(state))
            else:
                time.sleep(0.1)

        live.update(_render_dashboard(state))

    if "error" in result_box:
        raise result_box["error"]

    return result_box.get("result", [])
