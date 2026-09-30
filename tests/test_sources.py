import json
from datetime import date
from pathlib import Path

from leadgen.config import Config
from leadgen.scoring import rank
from leadgen.sources import csv_import, seao

FIX = Path(__file__).parent / "fixtures"


def test_csv_import_maps_columns():
    opps = csv_import.parse(FIX / "export.csv")
    assert len(opps) == 2 and opps[0].buyer == "City of Ottawa" and opps[0].closing.day == 20
    leads = rank(opps, Config(), date(2026, 9, 29))
    assert [l.opp.title for l in leads] == ["Leadership Development Program for Managers"]


def _rel(tag, status="active", title="Formation en leadership", date_="2026-09-25T10:00:00-04:00"):
    return {"ocid": "o1", "date": date_, "tag": [tag], "buyer": {"name": "CSS"}, "parties": [],
            "tender": {"title": title, "status": status, "procurementMethodDetails": "Avis",
                       "tenderPeriod": {"startDate": "2026-09-25T10:00:00-04:00", "endDate": "2026-10-20T11:00:00-04:00"},
                       "items": [{"description": "Formation", "classification": {"scheme": "UNSPSC", "id": "86101700", "description": "Formation"}}],
                       "documents": [{"url": "https://seao.example/1"}]}}


def test_seao_keeps_active_drops_awarded(tmp_path):
    f = tmp_path / "hebdo_1.json"
    f.write_text(json.dumps({"releases": [_rel("tender")]}))
    assert [o.title for o in seao.parse([f])] == ["Formation en leadership"]
    f.write_text(json.dumps({"releases": [_rel("tender"), _rel("contract", status="complete", date_="2026-09-28T10:00:00-04:00")]}))
    assert seao.parse([f]) == []
