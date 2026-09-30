"""Québec SEAO via the Données Québec OCDS releases (weekly JSON, CC-BY 4.0).

Covers provincial ministries, municipalities, school boards, health networks and Crown
corporations in Québec. Notices carry no free-text description or contact details, so
scoring relies on the title and UNSPSC item descriptions; contact the buyer via the SEAO link.
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime
from pathlib import Path

from ..models import Opportunity

PACKAGE = "https://www.donneesquebec.ca/recherche/api/3/action/package_show?id=d23b2e02-085d-43e5-9e6e-e1d558ebfdd5"
UA = {"User-Agent": "leadgen/0.1"}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        return r.read()


def _naive(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=None)
    except ValueError:
        return None


def download(cache_dir: Path, weeks: int) -> list[Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    res = json.loads(_get(PACKAGE))["result"]["resources"]
    weekly = sorted({r["name"]: r["url"] for r in res if r["name"].startswith("hebdo_")}.items(), reverse=True)[:weeks]
    paths = []
    for name, url in weekly:
        dest = cache_dir / name
        if not dest.exists():  # a closed week never changes; the current week is the newest name and is refreshed
            dest.write_bytes(_get(url))
        elif name == weekly[0][0]:
            dest.write_bytes(_get(url))
        paths.append(dest)
    return paths


def parse(paths: list[Path]) -> list[Opportunity]:
    by_ocid: dict[str, list[dict]] = {}
    for p in paths:
        for r in json.loads(p.read_text(encoding="utf-8")).get("releases", []):
            by_ocid.setdefault(r["ocid"], []).append(r)
    out = []
    for ocid, rels in by_ocid.items():
        rels.sort(key=lambda r: r.get("date", ""))
        last = rels[-1]
        t = last.get("tender") or {}
        tags = {x for r in rels for x in r.get("tag", [])}
        if t.get("status") != "active" or "tenderCancellation" in tags or "contract" in tags:
            continue  # cancelled, closed or already awarded
        period = t.get("tenderPeriod", {})
        first = next((r for r in rels if "tender" in r.get("tag", [])), rels[0])
        items = t.get("items", [])
        cls = [c for i in items for c in [i.get("classification", {}), *i.get("additionalClassifications", [])] if c.get("id")]
        docs = [d["url"] for d in t.get("documents", []) if d.get("url")]
        buyer = (last.get("buyer") or {}).get("name") or (t.get("procuringEntity") or {}).get("name", "")
        party = next((p for p in last.get("parties", []) if p.get("name") == buyer), {})
        addr = party.get("address", {})
        value = (t.get("value") or {}).get("amount")
        desc = "; ".join(filter(None, [i.get("description", "") for i in items] + [c.get("description", "") for c in cls]))
        if value:
            desc += f" Valeur estimée ${value:,.0f}."
        out.append(Opportunity(
            source="SEAO (QC)", ref=ocid, title=t.get("title", ""), description=desc,
            buyer=buyer, city=addr.get("locality", ""), province="Quebec",
            notice_type=t.get("procurementMethodDetails", ""), procurement_method=t.get("procurementMethod", ""),
            status="Open", published=(_naive(period.get("startDate")) or datetime.now()).date(),
            closing=_naive(period.get("endDate")), contract_start=None, contract_end=None,
            unspsc=list(dict.fromkeys(c["id"] for c in cls if c.get("scheme") == "UNSPSC")), gsin=[],
            unspsc_desc="; ".join(dict.fromkeys(c.get("description", "") for c in cls)), regions=addr.get("region", ""),
            contact_name="", contact_email="", contact_phone="",
            url=docs[0] if docs else "https://seao.gouv.qc.ca/avis-du-jour", attachments=docs,
        ))
    return out


def fetch(cache_dir: Path, weeks: int = 7, offline: bool = False) -> list[Opportunity]:
    paths = sorted(cache_dir.glob("hebdo_*.json"), reverse=True)[:weeks] if offline else download(cache_dir, weeks)
    return parse(paths)
