from __future__ import annotations

import argparse
import importlib
import logging
import sys
import types


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


def test_config_entry_dispatches_validate(monkeypatch) -> None:
    config_module = _import_config_module_with_stubs(monkeypatch)
    recorded: list[str] = []

    monkeypatch.setattr(
        config_module,
        "config_validate",
        lambda logger: recorded.append("validate"),
    )

    args = argparse.Namespace(config_cmd="validate")
    config_module.config_entry(logging.getLogger("test-config"), args)

    assert recorded == ["validate"]


def test_config_entry_dispatches_jobs(monkeypatch) -> None:
    config_module = _import_config_module_with_stubs(monkeypatch)
    recorded: list[str] = []

    monkeypatch.setattr(
        config_module,
        "config_jobs",
        lambda logger: recorded.append("jobs"),
    )

    args = argparse.Namespace(config_cmd="jobs")
    config_module.config_entry(logging.getLogger("test-config"), args)

    assert recorded == ["jobs"]
