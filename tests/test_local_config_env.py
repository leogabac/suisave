from __future__ import annotations

import importlib
import logging
import sys
import types
from pathlib import Path

from suisave.cmds.run import run_jobs
from suisave.core import CONFIG_PATH_ENV_VAR


def _import_config_module_with_stubs(monkeypatch):
    tomlkit_stub = types.SimpleNamespace(
        parse=lambda text: {"drives": {}},
        dumps=lambda doc, sort_keys=False: "[drives]\n",
        table=lambda: {},
        TOMLDocument=dict,
    )
    questionary_stub = types.SimpleNamespace(
        Choice=lambda *args, **kwargs: None,
        select=lambda *args, **kwargs: types.SimpleNamespace(ask=lambda: None),
    )

    monkeypatch.setitem(sys.modules, "tomlkit", tomlkit_stub)
    monkeypatch.setitem(sys.modules, "questionary", questionary_stub)
    sys.modules.pop("suisave.cmds.config", None)
    return importlib.import_module("suisave.cmds.config")


def test_config_init_writes_to_env_override(monkeypatch, tmp_path: Path) -> None:
    override = tmp_path / "alt-config" / "comet.toml"
    monkeypatch.setenv(CONFIG_PATH_ENV_VAR, str(override))
    config_module = _import_config_module_with_stubs(monkeypatch)

    config_module.config_init(logging.getLogger("test-config-init"))

    assert override.exists()
    assert "Local suisave configuration" in override.read_text(encoding="utf-8")
    assert config_module._load_config_doc()["drives"] == {}


def test_run_jobs_uses_env_override_for_local_mode(monkeypatch, tmp_path: Path) -> None:
    override = tmp_path / "alt-config" / "comet.toml"
    override.parent.mkdir(parents=True)
    override.write_text("[drives]\n[jobs]\n", encoding="utf-8")
    monkeypatch.setenv(CONFIG_PATH_ENV_VAR, str(override))

    recorded: dict[str, Path | list[str] | None] = {}

    class DummyComet:
        def __init__(self, path: Path, logger) -> None:
            recorded["path"] = path
            self.jobs = []

        def load(self, jobs_to_run) -> None:
            recorded["jobs_to_run"] = jobs_to_run

    monkeypatch.setattr("suisave.cmds.run.Comet", DummyComet)
    monkeypatch.setattr("suisave.cmds.run.run_with_rich_ui", lambda runner: [])
    monkeypatch.setattr("suisave.cmds.run.notify", lambda *args, **kwargs: None)

    run_jobs(logging.getLogger("test-run-jobs"), jobs_to_run=["docs"], interactive=False)

    assert recorded["path"] == override
    assert recorded["jobs_to_run"] == ["docs"]
