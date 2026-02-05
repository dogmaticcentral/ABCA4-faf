from __future__ import annotations

from dataclasses import dataclass

@dataclass
class RunParams:
    input_data: str  = None
    skip_existing: bool  | None = None
    start_from: str | None = None
    stop_after: str | None = None
