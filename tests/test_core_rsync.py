from __future__ import annotations

import logging
import subprocess

from suisave.core import run_rsync


def test_run_rsync_prints_stdout_for_dry_run(monkeypatch, capsys) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=kwargs.get("args") or args[0],
            returncode=0,
            stdout="file.txt\n",
            stderr="",
        )

    monkeypatch.setattr("suisave.core.subprocess.run", fake_run)

    output = run_rsync(["rsync", "--dry-run", "src/", "dst/"], logging.getLogger("test"))

    captured = capsys.readouterr()
    assert output == "file.txt\n"
    assert captured.out == "file.txt\n"
