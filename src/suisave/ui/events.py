from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class RunEvent:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.monotonic)
