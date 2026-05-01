from __future__ import annotations

from queue import Empty, Queue
import threading

from suisave.core import SuisaveError
from suisave.ui.state import RunState


def run_with_textual_ui(runner):
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import Footer, Header, Static
    except ImportError as exc:
        raise SuisaveError(
            "Textual TUI requested but Textual is not installed. Install the 'tui' extra."
        ) from exc

    class SuisaveTui(App):
        CSS = """
        Screen {
            layout: vertical;
        }
        #overview, #progress, #events {
            height: 1fr;
            border: round $primary;
            padding: 1 2;
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
            yield Header()
            yield Static(id="overview")
            yield Static(id="progress")
            yield Static(id="events")
            yield Footer()

        def on_mount(self) -> None:
            self.worker = threading.Thread(target=self._run_runner, daemon=True)
            self.worker.start()
            self.set_interval(0.2, self._drain_events)

        def _run_runner(self) -> None:
            self.runner.event_sink = self.event_queue.put
            try:
                self.result = self.runner.run()
            except Exception as exc:
                self.error = exc

        def _drain_events(self) -> None:
            changed = False
            while True:
                try:
                    event = self.event_queue.get_nowait()
                except Empty:
                    break
                self.state.handle(event)
                changed = True

            if changed:
                self._refresh_widgets()

            if self.worker is not None and not self.worker.is_alive() and self.event_queue.empty():
                self._refresh_widgets()
                self.exit()

        def _refresh_widgets(self) -> None:
            data = self.state.snapshot()
            self.query_one("#overview", Static).update(
                "\n".join(
                    [
                        f"Elapsed: {data['elapsed']}",
                        f"Jobs: {data['jobs']}",
                        f"Pairs: {data['pairs']}",
                        f"Job: {data['current_job']}",
                        f"Pair: {data['current_pair']}",
                        f"Source: {data['source']}",
                        f"Target: {data['target']}",
                    ]
                )
            )
            self.query_one("#progress", Static).update(
                "\n".join(
                    [
                        f"Activity: {data['activity']}",
                        f"Rsync: {data['progress_line']}",
                        f"Item: {data['current_item']}",
                        f"Source snapshot: {data['source_snapshot']}",
                        f"Target snapshot: {data['target_snapshot']}",
                        f"Monitor: {data['scan_status']}",
                    ]
                )
            )
            self.query_one("#events", Static).update(data["events"])

    app = SuisaveTui(runner)
    app.run()
    if app.error is not None:
        raise app.error
    return app.result
