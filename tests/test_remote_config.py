from __future__ import annotations

import logging
from pathlib import Path

import pytest

from suisave.core import SuisaveConfigError
from suisave.struct.remote import RemoteConfigLoader


def test_remote_config_loader_resolves_relative_paths_and_nested_hosts(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    source_dir = project_dir / "src"
    source_dir.mkdir()

    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    identity_dir = tmp_path / "keys"
    identity_dir.mkdir()
    identity_file = identity_dir / "id_ed25519"
    identity_file.write_text("test-key\n")

    config_path = config_dir / "remote.toml"
    config_path.write_text(
        """
[global]
default_rsync_flags = ["-az", "--info=progress2"]
default_mode = "push"

[remotes.work]
host = "main.example"
user = "alice"
port = 2222
identity_file = "../keys/id_ed25519"
ssh_options = ["ServerAliveInterval=30"]
base_path = "/srv/backups"

[remotes.work.jump_host]
host = "jump.example"
user = "jumper"
port = 2200

[remotes.work.alternate_host]
host = "tailscale.example"
user = "alice-alt"
ssh_options = ["StrictHostKeyChecking=no"]

[[jobs.sync]]
name = "repo"
sources = ["src"]
remotes = ["work"]
delete = true
""".strip()
        + "\n"
    )

    loader = RemoteConfigLoader(config_path, logging.getLogger("test-remote"), cwd=project_dir)
    remote_config = loader.load()

    remote = remote_config.remotes["work"]
    assert remote.identity_file == identity_file.resolve()
    assert remote.base_path == Path("/srv/backups")
    assert remote.jump_host is not None
    assert remote.jump_host.host == "jump.example"
    assert remote.jump_host.user == "jumper"
    assert remote.alternate_host is not None
    assert remote.alternate_host.host == "tailscale.example"
    assert remote.alternate_host.user == "alice-alt"

    job = remote_config.jobs[0]
    assert job.name == "repo"
    assert job.sources == [source_dir.resolve()]
    assert job.remotes == ["work"]
    assert job.rsync_flags == ["-az", "--info=progress2"]
    assert job.default_mode == "push"
    assert job.delete is True


def test_remote_config_loader_rejects_unknown_modes(tmp_path: Path) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    config_path = tmp_path / "remote.toml"
    config_path.write_text(
        f"""
[remotes.work]
host = "main.example"
base_path = "/srv/backups"

[[jobs.sync]]
name = "repo"
sources = ["{source_dir}"]
remotes = ["work"]
mode = "bidirectional"
""".strip()
        + "\n"
    )

    loader = RemoteConfigLoader(config_path, logging.getLogger("test-remote"), cwd=tmp_path)

    with pytest.raises(SuisaveConfigError, match="Invalid remote sync mode"):
        loader.load()
