from __future__ import annotations

from queue import Empty, Queue
import threading

from rich.console import Group
from rich.table import Table
from rich.text import Text

from suisave.core import SuisaveError, SuisaveRunCancelled
from suisave.ui.state import RunState


def _render_overview(data: dict[str, str]):
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=2)
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=2)
    table.add_row(
        "Job",
        f"[bold bright_yellow]{data['current_job']}[/]",
        "Pair",
        f"[bold bright_magenta]{data['current_pair']}[/]",
    )
    table.add_row(
        "Source",
        f"[bright_white]{data['source']}[/]",
        "Target",
        f"[bright_white]{data['target']}[/]",
    )
    table.add_row(
        "Activity",
        f"[bold bright_cyan]{data['activity']}[/]",
        "Heartbeat",
        f"[bold bright_yellow]{data['heartbeat']}[/]",
    )
    return Group(
        Text.from_markup("[bold bright_cyan]Run Overview[/]"),
        Text(""),
        table,
    )


def _render_progress_details(data: dict[str, str]):
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=2)
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=2)
    table.add_row(
        "Done",
        f"[bold bright_green]{data['rsync_bytes']}[/]",
        "Percent",
        f"[bold bright_magenta]{data['rsync_percent']}%[/]",
    )
    table.add_row(
        "Rate",
        f"[bold bright_cyan]{data['rsync_rate']}[/]",
        "ETA",
        f"[bold bright_yellow]{data['rsync_eta']}[/]",
    )
    table.add_row(
        "Source",
        f"[bold bright_blue]{data['source_snapshot']}[/]",
        "Target",
        f"[bold bright_blue]{data['target_snapshot']}[/]",
    )
    table.add_row(
        "Item",
        f"[bright_white]{data['current_item']}[/]",
        "Extra",
        f"[bright_black]{data['rsync_extra']}[/]",
    )
    return Group(
        Text.from_markup("[bold bright_green]Transfer Details[/]"),
        Text(""),
        table,
    )


def _render_monitor(data: dict[str, str]):
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=3)
    table.add_row("Scan", f"[bright_white]{data['scan_status']}[/]")
    if data["errors"] == "No errors.":
        table.add_row("Errors", "[bright_black]No errors.[/]")
    else:
        table.add_row("Errors", f"[bold bright_red]{data['errors']}[/]")
    return Group(
        Text.from_markup("[bold bright_yellow]Monitor[/]"),
        Text(""),
        table,
    )


def _render_summary(results):
    table = Table(expand=True, padding=(0, 1))
    table.add_column("Source", style="bold bright_white")
    table.add_column("Target", style="bright_white")
    table.add_column("Size", style="bold bright_green")
    table.add_column("Files", style="bold bright_magenta", justify="right")

    for result in results[-8:]:
        src = result.source_stats
        tg = result.target_stats
        table.add_row(src.name, tg.name, tg.size_human, str(tg.files))

    return Group(
        Text.from_markup("[bold bright_green]Completed Summary[/]"),
        Text(""),
        table,
    )


def _render_failure(data: dict[str, str]):
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold bright_white", ratio=1)
    table.add_column(ratio=4)
    table.add_row("Exit code", f"[bold bright_red]{data['failure_exit_code']}[/]")
    table.add_row("Target", f"[bright_white]{data['target']}[/]")

    lines = [line for line in data["failure_output"].splitlines() if line.strip()]
    excerpt = "\n".join(lines[-10:]) if lines else "No additional rsync output captured."
    return Group(
        Text.from_markup("[bold bright_red]Failure Details[/]"),
        Text(""),
        table,
        Text(""),
        Text.from_markup(f"[bright_red]{excerpt}[/]"),
    )


def run_with_textual_ui(runner):
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Footer, Header, ProgressBar, Static
    except ImportError as exc:
        raise SuisaveError(
            "Textual TUI requested but Textual is not installed. Install the 'tui' extra."
        ) from exc

    class SuisaveTui(App):
        BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Quit")]
        CSS = """
        Screen {
            background: #17140f;
            color: #f5efe6;
        }
        #hero {
            height: 7;
            layout: horizontal;
            margin: 0 1 1 1;
        }
        .metric {
            width: 1fr;
            border: round;
            padding: 1 2;
            content-align: center middle;
            background: #221d16;
        }
        #metric_elapsed {
            border: round #1fc7d4;
        }
        #metric_jobs {
            border: round #49d17d;
        }
        #metric_pairs {
            border: round #ff9bd5;
        }
        #main {
            height: 1fr;
            layout: horizontal;
            margin: 0 1;
        }
        .column {
            width: 1fr;
            height: 1fr;
        }
        .pane {
            height: 1fr;
            border: round #4b3c2b;
            padding: 1 2;
            margin-bottom: 1;
            background: #211b14;
        }
        #overview {
            border: round #1fc7d4;
        }
        #monitor {
            border: round #f0c35b;
        }
        #transfer_header, #transfer_body {
            border: round #49d17d;
        }
        #events {
            border: round #ff9bd5;
        }
        #transfer_header {
            height: auto;
            margin-bottom: 1;
        }
        #transfer_bar {
            margin-bottom: 1;
            color: #49d17d;
        }
        #completion {
            height: auto;
            margin: 0 1 1 1;
            border: round #49d17d;
            color: #f5efe6;
            background: #1f2b1f;
            padding: 1 2;
        }
        .failed {
            border: round #ff6b6b !important;
            background: #2a1717 !important;
        }
        """

        def __init__(self, runner):
            super().__init__()
            self.runner = runner
            self.event_queue: Queue = Queue()
            self.state = RunState()
            self.result = []
            self.error: Exception | None = None
            self.worker: threading.Thread | None = None

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="hero"):
                yield Static("", id="metric_elapsed", classes="metric")
                yield Static("", id="metric_jobs", classes="metric")
                yield Static("", id="metric_pairs", classes="metric")
            with Horizontal(id="main"):
                with Vertical(classes="column"):
                    yield Static(id="overview", classes="pane")
                    yield Static(id="monitor", classes="pane")
                with Vertical(classes="column"):
                    yield Static(id="transfer_header", classes="pane")
                    yield ProgressBar(total=100, show_eta=False, id="transfer_bar")
                    yield Static(id="transfer_body", classes="pane")
                    yield Static(id="events", classes="pane")
            yield Static("", id="completion")
            yield Footer()

        def on_mount(self) -> None:
            self.worker = threading.Thread(target=self._run_runner, daemon=True)
            self.worker.start()
            self.query_one("#completion", Static).display = False
            self.set_interval(0.15, self._drain_events)

        def action_quit(self) -> None:
            if self.worker is not None and self.worker.is_alive():
                self.runner.cancel()
            self.exit()

        def on_unmount(self) -> None:
            if self.worker is not None and self.worker.is_alive():
                self.runner.cancel()

        def _run_runner(self) -> None:
            self.runner.event_sink = self.event_queue.put
            try:
                self.result = self.runner.run()
            except Exception as exc:
                self.error = exc

        def _drain_events(self) -> None:
            while True:
                try:
                    event = self.event_queue.get_nowait()
                except Empty:
                    break
                self.state.handle(event)

            self._refresh_widgets()

        def _refresh_widgets(self) -> None:
            data = self.state.snapshot()

            self.query_one("#metric_elapsed", Static).update(
                Text.from_markup(
                    f"[bold bright_white]Elapsed[/]\n[bold bright_cyan]{data['elapsed']}[/]"
                )
            )
            self.query_one("#metric_jobs", Static).update(
                Text.from_markup(
                    f"[bold bright_white]Jobs[/]\n[bold bright_green]{data['jobs']}[/]"
                )
            )
            self.query_one("#metric_pairs", Static).update(
                Text.from_markup(
                    f"[bold bright_white]Pairs[/]\n[bold bright_magenta]{data['pairs']}[/]"
                )
            )

            self.query_one("#overview", Static).update(_render_overview(data))
            self.query_one("#monitor", Static).update(_render_monitor(data))

            self.query_one("#transfer_header", Static).update(
                Text.from_markup(
                    "\n".join(
                        [
                            "[bold bright_green]Transfer Hero[/]",
                            "",
                            f"[bold bright_green]rsync[/]  "
                            f"[bold bright_magenta]{data['rsync_percent']}%[/]  "
                            f"[bold bright_cyan]{data['rsync_rate']}[/]  "
                            f"[bold bright_yellow]eta {data['rsync_eta']}[/]",
                        ]
                    )
                )
            )

            progress_bar = self.query_one("#transfer_bar", ProgressBar)
            progress_bar.update(progress=float(data["rsync_percent"]))

            self.query_one("#transfer_body", Static).update(
                _render_progress_details(data)
            )

            self.query_one("#events", Static).update(
                _render_failure(data)
                if data["failed"] == "yes"
                else _render_summary(self.result)
                if data["finished"] == "yes" and self.result
                else Text.from_markup(
                    "[bold bright_cyan]Events[/]\n\n"
                    f"[bright_cyan]{data['events']}[/]"
                )
            )

            events_widget = self.query_one("#events", Static)
            completion = self.query_one("#completion", Static)
            if data["failed"] == "yes":
                events_widget.add_class("failed")
                completion.display = True
                completion.add_class("failed")
                completion.update(
                    Text.from_markup(
                        "[bold bright_red]Backup failed.[/] "
                        "[bold bright_white]Inspect the failure details and press q to leave.[/]"
                    )
                )
            elif data["finished"] == "yes":
                events_widget.remove_class("failed")
                completion.display = True
                completion.remove_class("failed")
                completion.update(
                    Text.from_markup(
                        "[bold bright_white]Backup run complete.[/] "
                        "[bold bright_green]Press q to leave the TUI.[/]"
                    )
                )
            else:
                events_widget.remove_class("failed")
                completion.display = False
                completion.remove_class("failed")

    app = SuisaveTui(runner)
    app.run()
    if runner.cancel_event.is_set():
        raise SuisaveRunCancelled("Backup run cancelled by user.")
    if app.error is not None:
        raise app.error
    return app.result
