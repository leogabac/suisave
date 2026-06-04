from __future__ import annotations

from pathlib import Path
import logging

from rich.text import Text

from suisave.core import CONFIG_PATH, SuisaveConfigError, get_mountpoint
from suisave.struct.local_config import (
    EditableConfig,
    EditableDrive,
    EditableJob,
    default_local_config,
    effective_global,
    load_local_config_model,
    render_local_config_preview,
    save_local_config_model,
    validate_local_config_model,
)


def _split_values(raw: str) -> list[str]:
    values: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        item = line.strip()
        if item:
            values.append(item)
    return values


def _join_values(values: list[str]) -> str:
    return "\n".join(values)


def _next_unique_name(existing: set[str], prefix: str) -> str:
    index = 1
    while True:
        candidate = f"{prefix}_{index}"
        if candidate not in existing:
            return candidate
        index += 1


def launch_config_tui(path: Path = CONFIG_PATH, logger: logging.Logger | None = None) -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea, Tree
    except ImportError as exc:
        raise SuisaveConfigError(
            "Config TUI requested but Textual is not installed. Install the 'tui' extra."
        ) from exc

    class ConfigEditorApp(App):
        BINDINGS = [
            ("up", "move_up", "Up"),
            ("down", "move_down", "Down"),
            ("j", "move_down", "Down"),
            ("k", "move_up", "Up"),
            ("i", "enter_insert", "Insert"),
            ("enter", "enter_insert", "Edit"),
            ("escape", "enter_normal", "Normal"),
            ("d", "delete_selected", "Delete"),
            ("D", "add_drive", "Add Drive"),
            ("B", "add_backup_job", "Add Backup"),
            ("C", "add_custom_job", "Add Custom"),
            ("ctrl+s", "save", "Save"),
            ("ctrl+r", "reload", "Reload"),
            ("q", "quit", "Quit"),
        ]
        CSS = """
        Screen {
            background: #17140f;
            color: #f5efe6;
        }
        #hero {
            height: 4;
            margin: 0 1 1 1;
            border: round #1fc7d4;
            background: #221d16;
            padding: 1 2;
        }
        #main {
            height: 1fr;
            layout: horizontal;
            margin: 0 1 1 1;
        }
        .pane {
            border: round #4b3c2b;
            background: #211b14;
            padding: 1 1;
            margin-right: 1;
        }
        #nav_pane {
            width: 28;
            border: round #1fc7d4;
        }
        #nav_help {
            height: auto;
            margin-bottom: 1;
            color: #f0c35b;
        }
        #editor_pane {
            width: 1fr;
            border: round #49d17d;
        }
        #preview_pane {
            width: 44;
            border: round #f0c35b;
            margin-right: 0;
        }
        .section {
            margin: 1 0 0 0;
        }
        .field_label {
            margin: 1 0 0 0;
            color: #f0c35b;
        }
        Input, TextArea {
            margin: 0 0 1 0;
        }
        #preview_body {
            height: 1fr;
        }
        #status_text.good {
            color: #49d17d;
        }
        #status_text.warn {
            color: #f0c35b;
        }
        #status_text.bad {
            color: #ff6b6b;
        }
        """

        def __init__(self) -> None:
            super().__init__()
            self.logger = logger or logging.getLogger("suisave.config.tui")
            self.path = path
            self.model: EditableConfig = default_local_config()
            self.current_selection: tuple[str, int | None] = ("global", None)
            self.dirty = False
            self.status_message = ""
            self.status_variant = "good"
            self._nav_nodes: dict[tuple[str, int | None], object] = {}
            self.mode = "normal"
            self._selection_order: list[tuple[str, int | None]] = [("global", None)]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(id="hero")
            with Horizontal(id="main"):
                with Vertical(id="nav_pane", classes="pane"):
                    yield Static(id="nav_help")
                    yield Tree("Config", id="nav_tree")
                with VerticalScroll(id="editor_pane", classes="pane"):
                    yield Static(id="editor_body")
                with Vertical(id="preview_pane", classes="pane"):
                    yield Static("Preview", classes="field_label")
                    yield Static(id="preview_body")
            yield Footer()

        def on_mount(self) -> None:
            self._load_from_disk()
            self._refresh_everything()
            self.call_after_refresh(self._focus_nav)

        def action_save(self) -> None:
            self._save_model()

        def action_reload(self) -> None:
            self._load_from_disk()
            self._set_status("Reloaded config from disk.", "good")
            self._refresh_everything()

        def _load_from_disk(self) -> None:
            self.model = load_local_config_model(self.path)
            self.dirty = False
            self.current_selection = ("global", None)
            if not self.path.exists():
                self._set_status(
                    "Config file does not exist yet. Edit the model and press Save to create it.",
                    "warn",
                )
            else:
                self._set_status(f"Loaded {self.path}", "good")

        def _set_status(self, message: str, variant: str) -> None:
            self.status_message = message
            self.status_variant = variant

        def _focus_nav(self) -> None:
            tree = self.query_one("#nav_tree", Tree)
            tree.focus()

        def _enter_insert_mode(self, focus_first: bool = True) -> None:
            self.mode = "insert"
            self._refresh_hero()
            self._refresh_nav_help()
            if focus_first:
                self.call_after_refresh(self._focus_first_editor_field)

        def _enter_normal_mode(self) -> None:
            self.mode = "normal"
            self._refresh_hero()
            self._refresh_nav_help()
            self.call_after_refresh(self._focus_nav)

        def _focus_first_editor_field(self) -> None:
            kind, _ = self.current_selection
            if kind == "global":
                target_id = "#global_pc_name"
            elif kind == "drive":
                target_id = "#drive_label"
            elif kind == "job":
                target_id = "#job_name"
            else:
                return
            try:
                self.query_one(target_id).focus()
            except Exception:
                return

        def _mark_dirty(self) -> None:
            self.dirty = True

        def _refresh_everything(self) -> None:
            self._refresh_hero()
            self._refresh_nav()
            self._refresh_nav_help()
            self._refresh_editor()
            self._refresh_preview()

        def _refresh_hero(self) -> None:
            effective = effective_global(self.model.global_config)
            suffix = "dirty" if self.dirty else "saved"
            text = Text()
            text.append("Local Config TUI\n", style="bold bright_cyan")
            text.append(f"{self.path}\n", style="bright_white")
            text.append(
                f"state: {suffix} | mode: {self.mode} | pc_name: {effective.pc_name} | base: {effective.default_target_base}\n",
                style="bright_yellow",
            )
            text.append(self.status_message, style={
                "good": "bright_green",
                "warn": "bright_yellow",
                "bad": "bright_red",
            }[self.status_variant])
            self.query_one("#hero", Static).update(text)

        def _refresh_nav_help(self) -> None:
            if self.mode == "normal":
                help_text = (
                    "Normal\n"
                    "j/k or arrows move\n"
                    "enter or i edit\n"
                    "D add drive  B add backup\n"
                    "C add custom  d delete"
                )
            else:
                help_text = (
                    "Insert\n"
                    "edit fields directly\n"
                    "tab moves focus\n"
                    "escape returns to normal"
                )
            self.query_one("#nav_help", Static).update(help_text)

        def _refresh_nav(self) -> None:
            tree = self.query_one("#nav_tree", Tree)
            tree.root.remove_children()
            self._nav_nodes = {}
            self._selection_order = [("global", None)]

            global_node = tree.root.add("Global")
            global_node.data = ("global", None)
            self._nav_nodes[("global", None)] = global_node

            drives_parent = tree.root.add("Drives")
            drives_parent.expand()
            drives_parent.data = ("drives_root", None)
            for index, drive in enumerate(self.model.drives):
                mountpoint = get_mountpoint(drive.uuid.strip()) if drive.uuid.strip() else None
                mount_marker = " mounted" if mountpoint else " missing"
                child = drives_parent.add(f"{drive.label or '<unnamed>'} [{mount_marker}]")
                child.data = ("drive", index)
                self._nav_nodes[("drive", index)] = child
                self._selection_order.append(("drive", index))

            jobs_parent = tree.root.add("Jobs")
            jobs_parent.expand()
            jobs_parent.data = ("jobs_root", None)
            for index, job in enumerate(self.model.jobs):
                child = jobs_parent.add(f"{job.kind}: {job.name or '<unnamed>'}")
                child.data = ("job", index)
                self._nav_nodes[("job", index)] = child
                self._selection_order.append(("job", index))

            tree.root.expand()
            target = self._nav_nodes.get(self.current_selection)
            if target is None:
                self.current_selection = ("global", None)
                target = self._nav_nodes.get(self.current_selection)
            if target is not None:
                tree.select_node(target)

        def _refresh_editor(self) -> None:
            container = self.query_one("#editor_body", Static)
            kind, index = self.current_selection

            if kind == "global":
                body = "\n".join(
                    [
                        "[bold bright_green]Global Defaults[/]",
                        "",
                        "Edit the explicit values written into [global]. Blank fields fall back to runtime defaults.",
                    ]
                )
            elif kind == "drive" and index is not None:
                drive = self.model.drives[index]
                mountpoint = get_mountpoint(drive.uuid.strip()) if drive.uuid.strip() else None
                body = "\n".join(
                    [
                        "[bold bright_green]Drive[/]",
                        "",
                        f"Mounted: {'yes' if mountpoint else 'no'}",
                        f"Mountpoint: {mountpoint or '-'}",
                    ]
                )
            elif kind == "job" and index is not None:
                job = self.model.jobs[index]
                body = "\n".join(
                    [
                        f"[bold bright_green]{job.kind.title()} Job[/]",
                        "",
                        "Sources, drives, and flags accept one item per line.",
                    ]
                )
            else:
                body = (
                    "[bold bright_green]Selection[/]\n\n"
                    "Choose Global, a drive, or a job from the left."
                )

            container.update(body)
            self.call_after_refresh(self._mount_editor_fields)

        async def _mount_editor_fields(self) -> None:
            editor = self.query_one("#editor_pane", VerticalScroll)
            children = [child for child in editor.children if child.id != "editor_body"]
            for child in children:
                await child.remove()

            kind, index = self.current_selection

            if kind == "global":
                await editor.mount(Label("pc_name", classes="field_label"))
                await editor.mount(
                    Input(
                        value=self.model.global_config.pc_name,
                        placeholder="Leave blank for hostname-machine-id",
                        id="global_pc_name",
                    )
                )
                await editor.mount(Label("default_target_base", classes="field_label"))
                await editor.mount(
                    Input(
                        value=self.model.global_config.default_target_base,
                        placeholder="Leave blank for backups",
                        id="global_default_target_base",
                    )
                )
                await editor.mount(Label("default_rsync_flags", classes="field_label"))
                await editor.mount(
                    TextArea(
                        _join_values(self.model.global_config.default_rsync_flags),
                        id="global_default_rsync_flags",
                    )
                )
                return

            if kind == "drive" and index is not None:
                drive = self.model.drives[index]
                await editor.mount(Label("label", classes="field_label"))
                await editor.mount(
                    Input(value=drive.label, placeholder="backup_disk", id="drive_label")
                )
                await editor.mount(Label("uuid", classes="field_label"))
                await editor.mount(
                    Input(value=drive.uuid, placeholder="UUID", id="drive_uuid")
                )
                return

            if kind == "job" and index is not None:
                job = self.model.jobs[index]
                await editor.mount(Label("name", classes="field_label"))
                await editor.mount(
                    Input(value=job.name, placeholder="documents", id="job_name")
                )
                await editor.mount(Label("sources", classes="field_label"))
                await editor.mount(
                    TextArea(_join_values(job.sources), id="job_sources")
                )
                await editor.mount(Label("drives", classes="field_label"))
                await editor.mount(
                    TextArea(_join_values(job.drives), id="job_drives")
                )
                if job.kind == "custom":
                    await editor.mount(Label("target_base", classes="field_label"))
                    await editor.mount(
                        Input(
                            value=job.target_base,
                            placeholder="Leave blank for default target base",
                            id="job_target_base",
                        )
                    )
                    await editor.mount(Label("flags", classes="field_label"))
                    await editor.mount(
                        TextArea(_join_values(job.flags), id="job_flags")
                    )

        def _refresh_preview(self) -> None:
            self.query_one("#preview_body", Static).update(
                Text(render_local_config_preview(self.model))
            )

        def _refresh_after_edit(self, *, refresh_nav: bool = False) -> None:
            self._refresh_hero()
            if refresh_nav:
                self._refresh_nav()
            self._refresh_preview()

        def _save_model(self) -> None:
            problems = validate_local_config_model(self.model)
            if problems:
                self._set_status(
                    f"Cannot save until validation errors are fixed. First error: {problems[0]}",
                    "bad",
                )
                self._refresh_hero()
                self._refresh_preview()
                return

            save_local_config_model(self.path, self.model)
            self.dirty = False
            self._set_status(f"Saved {self.path}", "good")
            self._refresh_everything()

        def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
            data = getattr(event.node, "data", None)
            if isinstance(data, tuple):
                self.current_selection = data
                self._refresh_editor()

        def on_input_changed(self, event: Input.Changed) -> None:
            widget_id = event.input.id or ""
            kind, index = self.current_selection

            if widget_id == "global_pc_name":
                self.model.global_config.pc_name = event.value
                refresh_nav = False
            elif widget_id == "global_default_target_base":
                self.model.global_config.default_target_base = event.value
                refresh_nav = False
            elif kind == "drive" and index is not None:
                if widget_id == "drive_label":
                    previous = self.model.drives[index].label
                    self.model.drives[index].label = event.value
                    if previous != event.value:
                        for job in self.model.jobs:
                            job.drives = [
                                event.value if drive == previous else drive
                                for drive in job.drives
                            ]
                    refresh_nav = True
                elif widget_id == "drive_uuid":
                    self.model.drives[index].uuid = event.value
                    refresh_nav = True
                else:
                    return
            elif kind == "job" and index is not None:
                if widget_id == "job_name":
                    self.model.jobs[index].name = event.value
                    refresh_nav = True
                elif widget_id == "job_target_base":
                    self.model.jobs[index].target_base = event.value
                    refresh_nav = False
                else:
                    return
            else:
                return

            self._mark_dirty()
            self._set_status("Unsaved changes.", "warn")
            self._refresh_after_edit(refresh_nav=refresh_nav)

        def on_text_area_changed(self, event: TextArea.Changed) -> None:
            widget_id = event.text_area.id or ""
            kind, index = self.current_selection

            if widget_id == "global_default_rsync_flags":
                self.model.global_config.default_rsync_flags = _split_values(
                    event.text_area.text
                )
            elif kind == "job" and index is not None:
                if widget_id == "job_sources":
                    self.model.jobs[index].sources = _split_values(event.text_area.text)
                elif widget_id == "job_drives":
                    self.model.jobs[index].drives = _split_values(event.text_area.text)
                elif widget_id == "job_flags":
                    self.model.jobs[index].flags = _split_values(event.text_area.text)
                else:
                    return
            else:
                return

            self._mark_dirty()
            self._set_status("Unsaved changes.", "warn")
            self._refresh_after_edit(refresh_nav=False)

        def action_move_up(self) -> None:
            if self.mode != "normal":
                return
            self._move_selection(-1)

        def action_move_down(self) -> None:
            if self.mode != "normal":
                return
            self._move_selection(1)

        def action_enter_insert(self) -> None:
            if self.mode == "insert":
                return
            self._enter_insert_mode()

        def action_enter_normal(self) -> None:
            if self.mode == "normal":
                return
            self._enter_normal_mode()

        def action_delete_selected(self) -> None:
            if self.mode != "normal":
                return
            self._delete_selected()

        def action_add_drive(self) -> None:
            if self.mode != "normal":
                return
            self._add_drive()

        def action_add_backup_job(self) -> None:
            if self.mode != "normal":
                return
            self._add_job("backup")

        def action_add_custom_job(self) -> None:
            if self.mode != "normal":
                return
            self._add_job("custom")

        def _move_selection(self, delta: int) -> None:
            if not self._selection_order:
                return
            try:
                current_index = self._selection_order.index(self.current_selection)
            except ValueError:
                current_index = 0
            next_index = max(0, min(len(self._selection_order) - 1, current_index + delta))
            self.current_selection = self._selection_order[next_index]
            target = self._nav_nodes.get(self.current_selection)
            if target is not None:
                self.query_one("#nav_tree", Tree).select_node(target)
            self._refresh_editor()

        def _add_drive(self) -> None:
            existing = {drive.label for drive in self.model.drives}
            label = _next_unique_name(existing, "drive")
            self.model.drives.append(EditableDrive(label=label, uuid=""))
            self.current_selection = ("drive", len(self.model.drives) - 1)
            self._mark_dirty()
            self._set_status(f"Added drive {label}.", "warn")
            self._refresh_everything()
            self._enter_insert_mode()

        def _add_job(self, kind: str) -> None:
            existing = {job.name for job in self.model.jobs}
            name = _next_unique_name(existing, kind)
            self.model.jobs.append(
                EditableJob(
                    kind=kind,
                    name=name,
                    sources=[],
                    drives=[],
                    target_base="" if kind == "backup" else "",
                    flags=[],
                )
            )
            self.current_selection = ("job", len(self.model.jobs) - 1)
            self._mark_dirty()
            self._set_status(f"Added {kind} job {name}.", "warn")
            self._refresh_everything()
            self._enter_insert_mode()

        def _delete_selected(self) -> None:
            kind, index = self.current_selection
            if kind == "drive" and index is not None:
                label = self.model.drives[index].label
                del self.model.drives[index]
                for job in self.model.jobs:
                    job.drives = [drive for drive in job.drives if drive != label]
                self.current_selection = ("global", None)
                self._mark_dirty()
                self._set_status(
                    f"Deleted drive {label} and removed it from jobs.", "warn"
                )
                self._refresh_everything()
                self._enter_normal_mode()
                return
            if kind == "job" and index is not None:
                name = self.model.jobs[index].name
                del self.model.jobs[index]
                self.current_selection = ("global", None)
                self._mark_dirty()
                self._set_status(f"Deleted job {name}.", "warn")
                self._refresh_everything()
                self._enter_normal_mode()
                return
            self._set_status("Select a drive or job to delete it.", "warn")
            self._refresh_hero()

    ConfigEditorApp().run()
