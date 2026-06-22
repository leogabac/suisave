from __future__ import annotations

from queue import Empty, Queue
import threading
import time

from rich.align import Align
from rich.columns import Columns
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

    overview = Table.grid(expand=True, padding=(0, 1))
    overview.add_column(style="bold bright_white", ratio=1)
    overview.add_column(ratio=3)
    overview.add_column(style="bold bright_white", ratio=1)
    overview.add_column(ratio=3)
    overview.add_row(
        "Elapsed",
        f"[bold bright_cyan]{data['elapsed']}[/]",
        "Jobs",
        f"[bold bright_green]{data['jobs']}[/]",
    )
    overview.add_row(
        "Pairs",
        f"[bold bright_green]{data['pairs']}[/]",
        "Pair",
        f"[bold bright_magenta]{data['current_pair']}[/]",
    )
    overview.add_row(
        "Job",
        f"[bold bright_yellow]{data['current_job']}[/]",
        "Activity",
        f"[bold bright_white]{data['activity']}[/]",
    )
    overview.add_row(
        "Source",
        f"[bright_white]{data['source']}[/]",
        "Target",
        f"[bright_white]{data['target']}[/]",
    )

    percent = (
        float(data["progress_line"].split("|")[1].strip().rstrip("%"))
        if "%" in data["progress_line"]
        else 0.0
    )
    progress_stats = Table.grid(expand=True, padding=(0, 1))
    progress_stats.add_column(style="bold bright_white", ratio=1)
    progress_stats.add_column(ratio=2)
    progress_stats.add_column(style="bold bright_white", ratio=1)
    progress_stats.add_column(ratio=2)

    progress_parts = [part.strip() for part in data["progress_line"].split("|")]
    bytes_done = progress_parts[0] if progress_parts else "waiting"
    percent_done = progress_parts[1] if len(progress_parts) > 1 else "-"
    rate = progress_parts[2] if len(progress_parts) > 2 else "-"
    eta = progress_parts[3].removeprefix("eta ").strip() if len(progress_parts) > 3 else "-"
    extra = progress_parts[4] if len(progress_parts) > 4 else "-"

    progress_stats.add_row(
        "Done",
        f"[bold bright_green]{bytes_done}[/]",
        "Percent",
        f"[bold bright_magenta]{percent_done}[/]",
    )
    progress_stats.add_row(
        "Rate",
        f"[bold bright_cyan]{rate}[/]",
        "ETA",
        f"[bold bright_yellow]{eta}[/]",
    )
    progress_stats.add_row(
        "Source",
        f"[bold bright_blue]{data['source_snapshot']}[/]",
        "Target",
        f"[bold bright_blue]{data['target_snapshot']}[/]",
    )
    progress_stats.add_row(
        "Item",
        f"[bright_white]{data['current_item']}[/]",
        "Extra",
        f"[bright_black]{extra}[/]" if extra != "-" else "-",
    )

    progress_group = Group(
        Text(f"heartbeat: {data['heartbeat']}", style="bold bright_yellow"),
        ProgressBar(total=100, completed=percent),
        progress_stats,
    )

    monitor_group = Group(
        Text.from_markup(f"[bold bright_yellow]scan[/] [bright_white]{data['scan_status']}[/]"),
        Text(""),
        Text.from_markup(f"[bold bright_white]errors[/]"),
        Text.from_markup(
            f"[bright_red]{data['errors']}[/]"
            if data["errors"] != "No errors."
            else "[bright_black]No errors.[/]"
        ),
    )

    if data["failed"] == "yes":
        failure_lines = [line for line in data["failure_output"].splitlines() if line.strip()]
        excerpt = "\n".join(failure_lines[-10:]) if failure_lines else "No additional rsync output captured."
        events_panel = Panel(
            Text.from_markup(
                f"[bold bright_red]Failure Details[/]\n\n"
                f"[bright_white]exit code:[/] [bold bright_red]{data['failure_exit_code']}[/]\n\n"
                f"[bright_red]{excerpt}[/]"
            ),
            title="[bold bright_red]Failure[/]",
            border_style="bright_red",
        )
    else:
        events_panel = Panel(
            Text.from_markup(f"[bright_cyan]{data['events']}[/]"),
            title="[bold bright_cyan]Events[/]",
            border_style="bright_cyan",
        )

    completion_panel = None
    if data["failed"] == "yes":
        completion_panel = Panel(
            Align.center(
                Text(
                    "Backup failed. Relevant rsync output is shown above.",
                    style="bold bright_red",
                )
            ),
            title="[bold bright_red]Failed[/]",
            border_style="bright_red",
        )
    elif data["finished"] == "yes":
        completion_panel = Panel(
            Align.center(
                Text(
                    "Backup run complete. Summary follows shortly.",
                    style="bold bright_green",
                )
            ),
            title="[bold bright_green]Completed[/]",
            border_style="bright_green",
        )

    top_row = Columns(
        [
            Panel(
                overview,
                title="[bold bright_cyan]Run[/]",
                border_style="bright_cyan",
            ),
            Panel(
                progress_group,
                title="[bold bright_green]Transfer[/]",
                border_style="bright_green",
            ),
        ],
        equal=True,
        expand=True,
    )
    bottom_row = Columns(
        [
            Panel(
                monitor_group,
                title="[bold bright_yellow]Monitor[/]",
                border_style="bright_yellow",
            ),
            events_panel,
        ],
        equal=True,
        expand=True,
    )

    panels = [top_row, bottom_row]
    if completion_panel is not None:
        panels.append(completion_panel)

    return Group(*panels)


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
            while True:
                try:
                    event = event_queue.get_nowait()
                except Empty:
                    break
                state.handle(event)
            live.update(_render_dashboard(state))
            time.sleep(0.1)

        live.update(_render_dashboard(state))
        if "error" not in result_box:
            for _ in range(20):
                live.update(_render_dashboard(state))
                time.sleep(0.2)

    if "error" in result_box:
        raise result_box["error"]

    return result_box.get("result", [])
