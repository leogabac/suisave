from __future__ import annotations

from pathlib import Path

from suisave.cmds.run import _build_rsync_cmd, _print_dry_run_output, get_st_pairs
from suisave.cmds.run import PairResult
from suisave.struct.stats import DirStats
from suisave.struct.context import BackupJob, Drive, GlobalConfig


def make_backup_job(tmp_path: Path) -> tuple[BackupJob, Path]:
    mountpoint = tmp_path / "mnt"
    source = tmp_path / "home" / "user" / "docs"
    source.mkdir(parents=True)
    drive = Drive(name="archive", uuid="uuid-archive", mountpoint=mountpoint)
    job = BackupJob(
        name="docs",
        sources=[source],
        drives=[drive],
        global_config=GlobalConfig(
            pc_name="workstation",
            default_tg_base=Path("backups"),
            default_rsync_flags=["-avh", "--delete"],
        ),
    )
    return job, source


def test_build_rsync_cmd_adds_dry_run_once(tmp_path: Path) -> None:
    job, source = make_backup_job(tmp_path)
    target = tmp_path / "target"

    cmd = _build_rsync_cmd(job, source, target, dry_run=True)

    assert cmd[:4] == ["rsync", "-avh", "--delete", "--dry-run"]
    assert cmd.count("--dry-run") == 1


def test_get_st_pairs_skips_target_creation_in_dry_run(tmp_path: Path, monkeypatch) -> None:
    job, source = make_backup_job(tmp_path)
    fake_home = tmp_path / "home" / "user"
    monkeypatch.setattr("suisave.cmds.run.Path.home", lambda: fake_home)

    pairs = get_st_pairs(job, create_targets=False)

    assert len(pairs) == 1
    _, target = pairs[0]
    assert target == job.drives[0].mountpoint / "backups/workstation" / source.relative_to(fake_home)
    assert not target.exists()


def test_print_dry_run_output_emits_rsync_preview(tmp_path: Path, capsys) -> None:
    job, source = make_backup_job(tmp_path)
    stats = DirStats(source, job)
    result = PairResult(
        source_stats=stats,
        target_stats=stats,
        rsync_output="sending incremental file list\nfile.txt\n",
    )

    _print_dry_run_output([result])

    captured = capsys.readouterr()
    assert "sending incremental file list" in captured.out
    assert "file.txt" in captured.out
