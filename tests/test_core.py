from __future__ import annotations

from pathlib import Path

from suisave.core import CONFIG_PATH_ENV_VAR, DEFAULT_CONFIG_PATH, get_config_path


def test_get_config_path_defaults_to_standard_local_path(monkeypatch) -> None:
    monkeypatch.delenv(CONFIG_PATH_ENV_VAR, raising=False)

    assert get_config_path() == DEFAULT_CONFIG_PATH


def test_get_config_path_honors_environment_override(monkeypatch, tmp_path: Path) -> None:
    override = tmp_path / "custom" / "comet.toml"
    monkeypatch.setenv(CONFIG_PATH_ENV_VAR, str(override))

    assert get_config_path() == override
