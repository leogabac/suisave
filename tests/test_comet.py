from __future__ import annotations

import logging
from pathlib import Path

from suisave.struct.comet import Comet, LOCAL_VENV_EXCLUDE, ensure_local_rsync_excludes
from suisave.struct.context import BackupJob, CustomJob


def test_ensure_local_rsync_excludes_appends_once() -> None:
    flags = ["-avh", "--delete"]

    result = ensure_local_rsync_excludes(flags)

    assert result == ["-avh", "--delete", LOCAL_VENV_EXCLUDE]
    assert ensure_local_rsync_excludes(result) == result


def test_comet_load_applies_defaults_and_job_specific_flags(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()

    config_path = tmp_path / "comet.toml"
    config_path.write_text(
        f"""
[global]
pc_name = "workstation"

[drives.archive]
uuid = "uuid-archive"

[drives.offline]
uuid = "uuid-offline"

[[jobs.backup]]
name = "docs"
sources = ["{source_dir}"]
drives = ["archive"]

[[jobs.custom]]
name = "custom-sync"
sources = ["{custom_dir}"]
drives = ["archive"]
target_base = "exports"
flags = ["-rv"]
""".strip()
        + "\n"
    )

    mount_root = tmp_path / "mnt" / "archive"
    mount_root.mkdir(parents=True)
    monkeypatch.setattr(
        "suisave.struct.comet.get_mountpoint",
        lambda uuid: mount_root if uuid == "uuid-archive" else None,
    )

    comet = Comet(config_path, logging.getLogger("test-comet"))
    comet.load(jobs_to_run=None)

    assert comet.global_config.pc_name == "workstation"
    assert comet.global_config.default_tg_base == Path("backups")
    assert comet.global_config.default_rsync_flags == [
        "-avh",
        "--delete",
        LOCAL_VENV_EXCLUDE,
    ]

    assert [drive.name for drive in comet.drives] == ["archive"]
    assert len(comet.jobs) == 2

    backup_job = next(job for job in comet.jobs if isinstance(job, BackupJob))
    assert backup_job.name == "docs"
    assert backup_job.tg_base == Path("backups/workstation")
    assert backup_job.rsync_flags == ["-avh", "--delete", LOCAL_VENV_EXCLUDE]
    assert [drive.name for drive in backup_job.drives] == ["archive"]

    custom_job = next(job for job in comet.jobs if isinstance(job, CustomJob))
    assert custom_job.name == "custom-sync"
    assert custom_job.tg_base == Path("exports")
    assert custom_job.rsync_flags == ["-rv", LOCAL_VENV_EXCLUDE]
