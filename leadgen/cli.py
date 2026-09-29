from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config as cfgmod, report
from .scoring import rank
from .sources import canadabuys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="leadgen", description="Find actionable Canadian public sector training opportunities")
    p.add_argument("-c", "--config", default="config.toml", help="TOML config (see config.example.toml)")
    p.add_argument("-o", "--out", default="output", help="output directory")
    p.add_argument("--offline", action="store_true", help="use cached feeds only")
    p.add_argument("--top", type=int, default=15, help="rows to print")
    p.add_argument("--min-score", type=int)
    p.add_argument("--focus", action="append", help="extra topic keyword (repeatable)")
    a = p.parse_args(argv)

    cfg = cfgmod.load(a.config)
    if a.min_score is not None:
        cfg.min_score = a.min_score
    cfg.focus += a.focus or []

    opps = canadabuys.fetch(Path(cfg.cache_dir), offline=a.offline)
    leads = rank(opps, cfg)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report.write_csv(leads, out / "leads.csv")
    report.write_json(leads, out / "leads.json")
    report.write_html(leads, out / "leads.html")

    print(f"{len(opps)} notices scanned -> {len(leads)} leads ({sum(l.tier == 'A' for l in leads)} tier A). Wrote {out}/leads.{{csv,json,html}}")
    for l in leads[: a.top]:
        cl = f"{l.days_left}d" if l.days_left is not None else "n/a"
        print(f"[{l.tier}] {l.score:>3}  {cl:>5}  {l.opp.buyer[:38]:<38}  {l.opp.title[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
