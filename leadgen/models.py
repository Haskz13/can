from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Opportunity:
    source: str
    ref: str
    title: str
    description: str
    buyer: str
    city: str
    province: str
    notice_type: str
    procurement_method: str
    status: str
    published: date | None
    closing: datetime | None
    contract_start: date | None
    contract_end: date | None
    unspsc: list[str]
    gsin: list[str]
    unspsc_desc: str
    regions: str
    contact_name: str
    contact_email: str
    contact_phone: str
    url: str
    attachments: list[str] = field(default_factory=list)


@dataclass
class Lead:
    opp: Opportunity
    score: int
    tier: str
    relevance: int
    value: int
    timing: int
    est_value: float | None
    days_left: int | None
    days_since_published: int | None
    reasons: list[str]
    stage: str  # "open bid" | "early signal"
