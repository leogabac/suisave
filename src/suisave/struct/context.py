from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class Job:
    name: str
    sources: List[Path]
    drives: List[str]

    tg_base: str
    rsync_flags: List[str]


class Config:
    global_: GlobalConfig
    drives: Dict[str, Drive]
    jobs: List[Job]
