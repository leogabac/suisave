from __future__ import annotations

from dataclasses import dataclass
from abc import ABC
from pathlib import Path
from typing import Any, List, Dict

import tomllib  # Python 3.11+


@dataclass(frozen=True)
class GlobalConfig:
    pc_name: str
    default_tg_base: str
    default_rsync_flags: List[str]

    def show(self):
        print("=" * 50)
        print("GLOBAL CONFIGURATION OPTIONS")
        print("=" * 50)
        print(f"pc name: \t{self.pc_name}")
        print(f"target base: \t{self.default_tg_base}")
        print(f"rsync flags: \t{' '.join(self.default_rsync_flags)}")


@dataclass(frozen=True)
class Drive:
    name: str
    uuid: str
    mountpoint: Path


@dataclass(frozen=True)
class BlockDevice:
    name: str
    uuid: str
    mountpoint: Path
    label: str
    fstype: str


@dataclass
class RsyncStats:
    transferred_bytes: int = 0
    files_transferred: int = 0
    exit_code: int = 0


class AbstractJob(ABC):
    def __init__(self, name: str, sources: List[Path], drives: List[str]):
        self.name = name
        self.sources = sources
        self.drives = drives

        self.tg_base: Path = None
        self.rsync_flags: List[str] = None


class BackupJob(AbstractJob):
    def __init__(
        self,
        name: str,
        sources: List[Path],
        drives: List[str],
        global_config: GlobalConfig,
    ):
        super().__init__(name, sources, drives)

        self.tg_base = global_config.default_tg_base / global_config.pc_name
        self.rsync_flags = global_config.default_rsync_flags

    def __str__(self):
        return (
            f"BackupJob(name={self.name}, sources={self.sources}, drives={self.drives})"
        )


class CustomJob(AbstractJob):
    def __init__(
        self,
        name: str,
        sources: List[Path],
        drives: List[str],
        tg_base: Path,
        rsync_flags: List[str],
    ):
        super().__init__(name, sources, drives)
        self.tg_base: Path = tg_base
        self.rsync_flags: List[str] = rsync_flags

    def __str__(self):
        return f"CustomJob(name={self.name}, sources={self.sources}, drives={self.drives}, tg_base={self.tg_base}, rsync_flags={self.rsync_flags})"
