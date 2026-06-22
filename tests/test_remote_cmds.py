from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pytest

from suisave.core import SuisaveConfigError
from suisave.cmds.remote import (
    _apply_dry_run_flag,
    _apply_delete_override,
    _build_pull_cmd,
    _build_ssh_transport,
    remote_sync,
    _resolve_delete,
    _select_remotes,
)
from suisave.struct.remote import (
    RemoteConfig,
    RemoteDefinition,
    RemoteGlobalConfig,
    RemoteJob,
    RemoteSSHConfig,
)


def make_remote(
    *,
    name: str = "work",
    host: str = "main.example",
    user: str | None = "alice",
    port: int | None = 2222,
    ssh_options: list[str] | None = None,
    alternate_host: RemoteSSHConfig | None = None,
    jump_host: RemoteSSHConfig | None = None,
) -> RemoteDefinition:
    return RemoteDefinition(
        name=name,
        host=host,
        user=user,
        port=port,
        identity_file=None,
        ssh_options=ssh_options or [],
        base_path=Path("/srv/backups"),
        alternate_host=alternate_host,
        jump_host=jump_host,
    )


def test_build_ssh_transport_uses_alternate_and_jump_host() -> None:
    jump_host = RemoteSSHConfig(
        host="jump.example",
        user="jumper",
        port=2200,
        identity_file=None,
        ssh_options=["Compression=yes"],
    )
    alternate_host = RemoteSSHConfig(
        host="tail.example",
        user="alice-alt",
        port=2022,
        identity_file=None,
        ssh_options=["StrictHostKeyChecking=no"],
        jump_host=jump_host,
    )
    remote = make_remote(alternate_host=alternate_host, jump_host=jump_host)

    transport = _build_ssh_transport(
        remote,
        use_jump_host=True,
        use_alternate_host=True,
    )

    assert transport.startswith("ssh -p 2022")
    assert "alice-alt@tail.example" not in transport
    assert "StrictHostKeyChecking=no" in transport
    assert "ProxyCommand=" in transport
    assert "jumper@jump.example" in transport
    assert "-W %h:%p" in transport


def test_select_remotes_requires_single_target_for_pull_mode() -> None:
    remote_config = RemoteConfig(
        path=Path("/tmp/remote.toml"),
        global_config=RemoteGlobalConfig(default_rsync_flags=["-azvh"], default_mode=None),
        remotes={
            "work": make_remote(name="work"),
            "backup": make_remote(name="backup", host="backup.example"),
        },
        jobs=[],
    )
    job = RemoteJob(
        name="repo",
        sources=[Path("/tmp/src")],
        remotes=["work", "backup"],
        rsync_flags=["-azvh"],
        default_mode="pull",
        delete=None,
    )
    args = argparse.Namespace(target=None)

    with pytest.raises(SuisaveConfigError, match="Use --target to choose one for pull mode"):
        _select_remotes(remote_config, job, args, "pull")


def test_resolve_delete_and_apply_override_follow_precedence() -> None:
    job = RemoteJob(
        name="repo",
        sources=[Path("/tmp/src")],
        remotes=["work"],
        rsync_flags=["-azvh", "--delete"],
        default_mode=None,
        delete=False,
    )

    assert _resolve_delete(job, "push", None) is False
    assert _resolve_delete(job, "push", True) is True
    assert _resolve_delete(job, "pull", None) is False
    assert _resolve_delete(
        RemoteJob(
            name="repo",
            sources=[Path("/tmp/src")],
            remotes=["work"],
            rsync_flags=["-azvh", "--delete"],
            default_mode=None,
            delete=None,
        ),
        "push",
        None,
    ) is True
    assert _apply_delete_override(["-azvh", "--delete"], False) == ["-azvh"]
    assert _apply_delete_override(["-azvh"], True) == ["-azvh", "--delete"]
    assert _apply_dry_run_flag(["-azvh"], True) == ["-azvh", "--dry-run"]


def test_build_pull_cmd_skips_local_parent_creation_in_dry_run(tmp_path: Path) -> None:
    remote = make_remote()
    local_target = tmp_path / "nested" / "repo"

    cmd = _build_pull_cmd(
        remote,
        local_target,
        Path("/srv/backups/repo"),
        ["-azvh", "--dry-run"],
        use_jump_host=False,
        use_alternate_host=False,
        dry_run=True,
    )

    assert cmd[0] == "rsync"
    assert "--dry-run" in cmd
    assert not local_target.parent.exists()


def test_remote_sync_list_jobs_skips_execution(monkeypatch, tmp_path: Path) -> None:
    remote_config = RemoteConfig(
        path=tmp_path / "remote.toml",
        global_config=RemoteGlobalConfig(
            default_rsync_flags=["-azvh"],
            default_mode="push",
        ),
        remotes={"work": make_remote(name="work")},
        jobs=[
            RemoteJob(
                name="repo",
                sources=[tmp_path / "repo"],
                remotes=["work"],
                rsync_flags=["-azvh"],
                default_mode="push",
                delete=None,
            )
        ],
    )

    class DummyLoader:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def load(self, jobs_to_run=None, require_jobs=True):
            return remote_config

    printed: list[object] = []
    monkeypatch.setattr("suisave.cmds.remote.RemoteConfigLoader", DummyLoader)
    monkeypatch.setattr("suisave.cmds.remote.console.print", lambda obj: printed.append(obj))
    monkeypatch.setattr(
        "suisave.cmds.remote._resolve_requested_mode",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not execute")),
    )

    args = argparse.Namespace(
        config=str(tmp_path / "remote.toml"),
        name=None,
        source=None,
        target=None,
        push=False,
        pull=False,
        most_recent=False,
        use_jump_host=False,
        use_alternate_host=False,
        jump_and_alt_host=False,
        delete=False,
        no_delete=False,
        dry_run=False,
        list_jobs=True,
    )

    remote_sync(logging.getLogger("test-remote"), args)

    assert printed
