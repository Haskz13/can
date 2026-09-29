"""CanadaBuys open-data feeds (federal tenders; some provinces/municipalities also post here).

Feeds are plain CSVs published by Public Services and Procurement Canada:
  - openTenderNotice: every tender currently open
  - newTenderNotice:  notices published today (used to catch same-day postings)
"""
from __future__ import annotations

import csv
import io
import re
import urllib.request
from datetime import date, datetime
from pathlib import Path

from ..models import Opportunity

BASE = "https://canadabuys.canada.ca/opendata/pub/"
FEEDS = {
    "open": "openTenderNotice-ouvertAvisAppelOffres.csv",
    "new": "newTenderNotice-nouvelAvisAppelOffres.csv",
}
NOTICE_URL = "https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/{ref}"

csv.field_size_limit(10**9)


def download(feed: str, cache_dir: Path, force: bool = True) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / FEEDS[feed]
    if dest.exists() and not force:
        return dest
    req = urllib.request.Request(BASE + FEEDS[feed], headers={"User-Agent": "leadgen/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dest.write_bytes(r.read())
    return dest


def _date(s: str) -> date | None:
    s = (s or "").strip()
    try:
        return date.fromisoformat(s[:10]) if s else None
    except ValueError:
        return None


def _dt(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        d = _date(s)
        return datetime(d.year, d.month, d.day, 23, 59) if d else None


def _codes(s: str) -> list[str]:
    return [c.strip().lstrip("*") for c in (s or "").splitlines() if c.strip().lstrip("*")]


def _get(row: dict, prefix: str) -> str:
    """Column names are bilingual ('title-titre-eng'); match on the English-side prefix."""
    for k, v in row.items():
        if k.startswith(prefix):
            return (v or "").strip()
    return ""


def parse(path: Path) -> list[Opportunity]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        ref = row.get("referenceNumber-numeroReference", "").strip()
        if not ref:
            continue
        atts = [a.strip() for a in re.split(r"[\s,]+(?=https?://)", row.get("attachment-piecesJointes-eng", "")) if a.strip()]
        out.append(Opportunity(
            source="CanadaBuys",
            ref=ref,
            title=row.get("title-titre-eng", "").strip() or row.get("title-titre-fra", "").strip(),
            description=" ".join(filter(None, [
                row.get("tenderDescription-descriptionAppelOffres-eng", ""),
                row.get("tenderDescription-descriptionAppelOffres-fra", ""),
            ])).strip(),
            buyer=_get(row, "contractingEntityName-nomEntitContractante-eng"),
            city=_get(row, "contractingEntityAddressCity"),
            province=_get(row, "contractingEntityAddressProvince"),
            notice_type=_get(row, "noticeType-avisType-eng"),
            procurement_method=_get(row, "procurementMethod-methodeApprovisionnement-eng"),
            status=_get(row, "tenderStatus-appelOffresStatut-eng"),
            published=_date(row.get("publicationDate-datePublication", "")),
            closing=_dt(row.get("tenderClosingDate-appelOffresDateCloture", "")),
            contract_start=_date(row.get("expectedContractStartDate-dateDebutContratPrevue", "")),
            contract_end=_date(row.get("expectedContractEndDate-dateFinContratPrevue", "")),
            unspsc=_codes(row.get("unspsc", "")),
            gsin=_codes(row.get("gsin-nibs", "")),
            unspsc_desc=_get(row, "unspscDescription-eng").replace("\n", "; ").replace("*", ""),
            regions=_get(row, "regionsOfDelivery-regionsLivraison-eng").replace("\n", "; ").replace("*", ""),
            contact_name=_get(row, "contactInfoName"),
            contact_email=_get(row, "contactInfoEmail"),
            contact_phone=_get(row, "contactInfoPhone"),
            url=_get(row, "noticeURL-URLavis-eng") or NOTICE_URL.format(ref=ref),
            attachments=atts,
        ))
    return out


def fetch(cache_dir: Path, offline: bool = False) -> list[Opportunity]:
    seen: dict[str, Opportunity] = {}
    for feed in ("open", "new"):
        path = cache_dir / FEEDS[feed]
        if not offline:
            path = download(feed, cache_dir)
        if path.exists():
            for o in parse(path):
                seen[o.ref] = o
    return list(seen.values())
