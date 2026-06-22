from __future__ import annotations


def run_jobs(*args, **kwargs):
    from suisave.cmds.run import run_jobs as _run_jobs

    return _run_jobs(*args, **kwargs)


def config_drive_entry(*args, **kwargs):
    from suisave.cmds.config import config_drive_entry as _config_drive_entry

    return _config_drive_entry(*args, **kwargs)


def config_entry(*args, **kwargs):
    from suisave.cmds.config import config_entry as _config_entry

    return _config_entry(*args, **kwargs)


def config_show(*args, **kwargs):
    from suisave.cmds.config import config_show as _config_show

    return _config_show(*args, **kwargs)


def remote_sync(*args, **kwargs):
    from suisave.cmds.remote import remote_sync as _remote_sync

    return _remote_sync(*args, **kwargs)


__all__ = ["run_jobs", "config_drive_entry", "config_entry", "config_show", "remote_sync"]
