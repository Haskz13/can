from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # Actionability window
    max_age_days: int = 45          # published within this many days
    min_days_left: int = 5          # enough time left to write a bid
    max_days_left: int = 180
    early_signal_days: int = 120    # RFI / ACAN / ITQ / SA notices stay useful this long after publication
    min_score: int = 40
    # Your offering: extra keywords that boost relevance (e.g. "leadership", "cybersecurity")
    focus: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)   # drop anything mentioning these
    provinces: list[str] = field(default_factory=list)  # empty = all
    buyers: list[str] = field(default_factory=list)     # substring match; boost, not filter
    cache_dir: str = "data"
    sources: list[str] = field(default_factory=lambda: ["canadabuys", "seao"])
    seao_weeks: int = 7             # weekly SEAO files to read (~18 MB each)
    import_dir: str = "imports"     # CSV exports from MERX / Biddingo / Tenders On Time etc.
    import_columns: dict[str, list[str]] = field(default_factory=dict)  # extra column aliases


def load(path: str | None) -> Config:
    if path and Path(path).exists():
        raw = tomllib.loads(Path(path).read_text())
        return Config(**{k: v for k, v in raw.items() if k in Config.__dataclass_fields__})
    return Config()
