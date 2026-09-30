from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config as cfgmod, report
from .scoring import rank
from . import portals
from .sources import canadabuys, csv_import, seao


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="leadgen", description="Find actionable Canadian public sector training opportunities")
    p.add_argument("-c", "--config", default="config.toml", help="TOML config (see config.example.toml)")
    p.add_argument("-o", "--out", default="output", help="output directory")
    p.add_argument("--offline", action="store_true", help="use cached feeds only")
    p.add_argument("--top", type=int, default=15, help="rows to print")
    p.add_argument("--min-score", type=int)
    p.add_argument("--sources", help="comma list: canadabuys,seao (overrides config); imports/ CSVs are always read")
    p.add_argument("--portals", action="store_true", help="list every Canadian portal and how it is covered, then exit")
    p.add_argument("--focus", action="append", help="extra topic keyword (repeatable)")
    a = p.parse_args(argv)

    if a.portals:
        for prov, name, url, status, note in portals.PORTALS:
            print(f"[{status:<6}] {prov:<26} {name:<34} {url}\n          {note}")
        return 0

    cfg = cfgmod.load(a.config)
    if a.sources:
        cfg.sources = a.sources.split(",")
    if a.min_score is not None:
        cfg.min_score = a.min_score
    cfg.focus += a.focus or []

    cache = Path(cfg.cache_dir)
    opps = []
    for name in cfg.sources:
        try:
            if name == "canadabuys":
                opps += canadabuys.fetch(cache, offline=a.offline)
            elif name == "seao":
                opps += seao.fetch(cache / "seao", cfg.seao_weeks, offline=a.offline)
            else:
                print(f"unknown source {name!r}", file=sys.stderr)
        except Exception as e:  # one portal being down must not sink the run
            print(f"warning: {name} failed: {e}", file=sys.stderr)
    imp = Path(cfg.import_dir)
    if imp.is_dir():
        opps += csv_import.fetch(imp, cfg.import_columns)
    seen = {}
    for o in opps:  # same tender often appears on several portals
        seen.setdefault((o.title.lower().strip(), o.closing.date() if o.closing else None), o)
    opps = list(seen.values())
    leads = rank(opps, cfg)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report.write_csv(leads, out / "leads.csv")
    report.write_json(leads, out / "leads.json")
    report.write_html(leads, out / "leads.html")

    print(f"{len(opps)} notices scanned -> {len(leads)} leads ({sum(l.tier == 'A' for l in leads)} tier A). Wrote {out}/leads.{{csv,json,html}}")
    for l in leads[: a.top]:
        cl = f"{l.days_left}d" if l.days_left is not None else "n/a"
        print(f"[{l.tier}] {l.score:>3}  {cl:>5}  {l.opp.source[:10]:<10} {l.opp.buyer[:30]:<30}  {l.opp.title[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
