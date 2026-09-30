"""Import tenders from any portal/aggregator export (MERX, Biddingo, BIDS, Bids&Tenders, Tenders On Time, ...).

Drop saved-search exports (CSV) into a folder; column names are matched case-insensitively against the
aliases below, so most exports work unchanged. Add aliases in config under [import_columns] if not.
"""
from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path

from ..models import Opportunity

ALIASES = {
    "title": ["title", "tender title", "project title", "name", "opportunity", "description of work", "titre"],
    "description": ["description", "details", "summary", "scope", "tender description"],
    "buyer": ["buyer", "organization", "organisation", "agency", "issuer", "owner", "issuing organization", "client", "entity"],
    "province": ["province", "state", "region", "location", "jurisdiction"],
    "published": ["published", "publication date", "date published", "issue date", "posted", "posted date", "open date", "start date"],
    "closing": ["closing", "closing date", "close date", "deadline", "closes", "expiry", "expiry date", "end date", "bid closing"],
    "url": ["url", "link", "tender url", "notice url", "source url"],
    "ref": ["reference", "reference number", "ref", "tender id", "tender no", "solicitation number", "id", "notice id"],
    "notice_type": ["notice type", "type", "tender type", "category"],
    "contact_email": ["contact email", "email", "buyer email"],
    "contact_name": ["contact", "contact name", "buyer contact"],
}
FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%Y/%m/%d")


def _when(s: str) -> datetime | None:
    s = (s or "").strip()
    for f in FORMATS:
        for cand in (s, s[: len(s.split(" (")[0])]):
            try:
                return datetime.strptime(cand, f)
            except ValueError:
                pass
    m = re.match(r"\d{4}-\d{2}-\d{2}", s)
    return datetime.fromisoformat(m.group(0)) if m else None


def parse(path: Path, extra: dict[str, list[str]] | None = None) -> list[Opportunity]:
    aliases = {k: [a.lower() for a in v] + [a.lower() for a in (extra or {}).get(k, [])] for k, v in ALIASES.items()}
    out = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rd = csv.DictReader(f)
        cols = {h.strip().lower(): h for h in rd.fieldnames or []}
        pick = {k: next((cols[a] for a in al if a in cols), None) for k, al in aliases.items()}
        for i, row in enumerate(rd):
            g = lambda k: (row.get(pick[k]) or "").strip() if pick[k] else ""
            if not g("title"):
                continue
            closing, published = _when(g("closing")), _when(g("published"))
            out.append(Opportunity(
                source=f"import:{path.stem}", ref=g("ref") or f"{path.stem}-{i}", title=g("title"), description=g("description"),
                buyer=g("buyer"), city="", province=g("province"), notice_type=g("notice_type"), procurement_method="",
                status="Open", published=published.date() if published else None, closing=closing, contract_start=None,
                contract_end=None, unspsc=[], gsin=[], unspsc_desc="", regions="", contact_name=g("contact_name"),
                contact_email=g("contact_email"), contact_phone="", url=g("url"),
            ))
    return out


def fetch(folder: Path, extra: dict[str, list[str]] | None = None) -> list[Opportunity]:
    return [o for p in sorted(folder.glob("*.csv")) for o in parse(p, extra)]
