"""Score opportunities on three axes: training relevance, deal value, and timing.

The federal feed carries no dollar value, so value is inferred from proxies:
contract duration, vehicle type (standing offers / supply arrangements imply repeat
call-ups), dollar figures or volume hints in the text, and buyer size.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from .config import Config
from .models import Lead, Opportunity

# Strong training terms (EN/FR) -> weight
KEYWORDS = {
    r"\btrain(?:ing|er|ers)?\b": 12, r"\bformation\b": 12, r"\bcourses?\b": 8, r"\bcours\b": 6,
    r"\bworkshops?\b": 8, r"\batelier": 8, r"\bcurricul": 10, r"\bcoaching\b": 8, r"\bcoach(?:es)?\b": 5,
    r"\bfacilitat(?:ion|or|ors)\b": 6, r"\be-?learning\b": 12, r"\blearning (?:management|platform|solution|content)": 12,
    r"\bprofessional development\b": 12, r"\bd[ée]veloppement professionnel": 12, r"\bcertification\b": 6,
    r"\binstructors?\b": 8, r"\binstruct(?:ion|eurs?)\b": 6, r"\bworkshop\b": 4, r"\bseminars?\b": 6,
    r"\bleadership development\b": 10, r"\bupskill|reskill": 8, r"\bcompetenc(?:y|ies)\b": 3, r"\bwebinars?\b": 5,
    r"\bknowledge transfer\b": 6, r"\bawareness (?:program|session|training)": 8, r"\bmentor": 4, r"\b(?:development|learning|certificate) (?:program|programme)s?\b": 10, r"perfectionnement": 10, r"\baccompagnement\b": 4, r"\bapprentissage\b": 6, r"\bsensibilisation\b": 6, r"\bformateurs?\b": 8,
}
# UNSPSC segment/family prefixes that denote training/education
UNSPSC_TRAINING = ("8610", "8611", "8612", "8613", "8614", "9315")  # 8610 education/training services, 8613 = ed. facilities
GSIN_TRAINING = ("U",)  # GSIN group U = educational & training services

# Classic false positives: physical/animal/equipment "training" that is not a service you'd sell
NEGATIVE = [r"\bachat d|\bfourniture d[eu]|\bmission d.audit|\bétats financiers", r"\btraining (?:centre|center|area|theatre|theater|complex|building)\b", r"\bconstruction\b|\bsoftware develop|\bmaintenance services\b",r"\bhorse|equine|farrier|canine|k-?9\b", r"\btraining (?:aircraft|ammunition|ammo|range|facility)\b",
            r"\bsimulator\b", r"\bexplosive"]

EARLY_TYPES = ("request for information", "advance contract award", "invitation to qualify",
               "request for supply arrangement", "request for standing offer")
STANDING = ("standing offer", "supply arrangement")
HIGH_VALUE_HINTS = {
    r"\bmulti-?year\b|\bplusieurs ann[ée]es\b": 8, r"\boption (?:year|period)s?\b|\bannées? d'option": 6,
    r"\b(?:nation-?wide|national|across canada)\b": 5, r"\benterprise\b": 4,
    r"\bcohorts?\b": 4, r"\b(\d{2,5})\s+(?:participants|employees|learners|students|trainees|staff|employés)\b": 6,
    r"\bcall-?ups?\b": 5, r"\bcatalogue|\bcatalog\b": 3, r"\bbilingual|bilingue": 2,
}
MONEY = re.compile(r"\$\s?([\d]{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*(million|m\b|thousand|k\b)?", re.I)


def _money(text: str) -> float | None:
    best = None
    for m in MONEY.finditer(text):
        v = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").lower()
        v *= 1_000_000 if unit in ("million", "m") else 1_000 if unit in ("thousand", "k") else 1
        if v >= 1000:
            best = max(best or 0, v)
    return best


def _text(o: Opportunity) -> str:
    return f"{o.title} {o.description}".lower()


def relevance(o: Opportunity, cfg: Config) -> tuple[int, list[str]]:
    text, reasons, score = _text(o), [], 0
    title = o.title.lower()
    desc_score = 0
    for pat, w in KEYWORDS.items():
        if re.search(pat, title):
            score += w * 2
            reasons.append(f"title: {re.search(pat, title).group(0)}")
        elif re.search(pat, text):
            desc_score += w // 2
    coded = any(c.startswith(UNSPSC_TRAINING) for c in o.unspsc) or any(g.upper().startswith(GSIN_TRAINING) for g in o.gsin)
    # Passing mentions in a long description are weak evidence unless the title or codes agree
    score += desc_score if (score or coded) else min(desc_score, 15)
    if any(c.startswith(UNSPSC_TRAINING) for c in o.unspsc):
        score += 25
        reasons.append("UNSPSC training/education code")
    if any(g.upper().startswith(GSIN_TRAINING) for g in o.gsin):
        score += 25
        reasons.append("GSIN training code")
    for f in cfg.focus:
        if f.lower() in title:
            score += 25
            reasons.append(f"focus match in title: {f}")
        elif f.lower() in text:
            score += 12
            reasons.append(f"focus match: {f}")
    if score and any(re.search(p, text) for p in NEGATIVE):
        score = int(score * 0.4)
        reasons.append("possible false positive (equipment/animal/simulator)")
    return min(score, 100), reasons


def value(o: Opportunity, est: float | None) -> tuple[int, list[str]]:
    text, reasons, score = _text(o), [], 0
    if est:
        score += 30 if est >= 500_000 else 22 if est >= 100_000 else 12
        reasons.append(f"stated value ~${est:,.0f}")
    if o.contract_start and o.contract_end and o.contract_end > o.contract_start:
        yrs = (o.contract_end - o.contract_start).days / 365
        pts = 20 if yrs >= 3 else 14 if yrs >= 2 else 8 if yrs >= 1 else 0
        if pts:
            score += pts
            reasons.append(f"~{yrs:.1f}-year term")
    nt = o.notice_type.lower()
    if any(s in nt for s in STANDING):
        score += 12
        reasons.append("standing offer / supply arrangement (repeat call-ups)")
    for pat, w in HIGH_VALUE_HINTS.items():
        m = re.search(pat, text)
        if m:
            score += w
            reasons.append(f"scope signal: {m.group(0).strip()[:30]}")
    if len(o.description) > 1500:
        score += 5
    if o.procurement_method.lower().startswith("competitive"):
        score += 3
    return min(score, 100), reasons


def timing(o: Opportunity, cfg: Config, today: date) -> tuple[int, int | None, int | None, str, list[str]]:
    days_left = (o.closing.date() - today).days if o.closing else None
    age = (today - o.published).days if o.published else None
    early = any(t in o.notice_type.lower() for t in EARLY_TYPES)
    stage = "early signal" if early else "open bid"
    reasons = []
    pts = 0
    if days_left is not None:
        if days_left < 0:
            return 0, days_left, age, stage, ["closed"]
        if days_left < cfg.min_days_left and not early:
            return 0, days_left, age, stage, [f"closes in {days_left}d (too late to bid)"]
        pts += 25 if 10 <= days_left <= 45 else 18 if days_left > 45 else 12
        reasons.append(f"closes in {days_left}d")
    if age is not None:
        if age <= 7:
            pts += 10
            reasons.append("posted this week")
        elif age <= cfg.max_age_days:
            pts += 4
    if early:
        reasons.append(f"{o.notice_type.lower()} — get in before the RFP")
    return min(pts, 35), days_left, age, stage, reasons


def score_opportunity(o: Opportunity, cfg: Config, today: date | None = None) -> Lead | None:
    today = today or date.today()
    text = _text(o)
    if any(x.lower() in text for x in cfg.exclude):
        return None
    if cfg.provinces and not any(p.lower() in (o.province + " " + o.regions).lower() for p in cfg.provinces):
        return None
    rel, r1 = relevance(o, cfg)
    if rel < 24:
        return None
    est = _money(o.description)
    val, r2 = value(o, est)
    tim, days_left, age, stage, r3 = timing(o, cfg, today)
    if tim == 0:
        return None
    if age is not None and age > (cfg.early_signal_days if stage == "early signal" else cfg.max_age_days):
        return None
    if days_left is not None and days_left > cfg.max_days_left and stage != "early signal":
        return None
    boost = 5 if any(b.lower() in o.buyer.lower() for b in cfg.buyers) else 0
    # relevance gates everything: a valuable, timely non-training deal is not a lead
    total = round(min(rel * 1.6, 100) * 0.5 + val * 0.25 + tim * (25 / 35) + boost)
    tier = "A" if total >= 70 else "B" if total >= 55 else "C"
    if total < cfg.min_score:
        return None
    return Lead(o, min(total, 100), tier, rel, val, tim, est, days_left, age, r1 + r2 + r3, stage)


def rank(opps: list[Opportunity], cfg: Config, today: date | None = None) -> list[Lead]:
    leads = [l for o in opps if (l := score_opportunity(o, cfg, today))]
    return sorted(leads, key=lambda l: (-l.score, l.days_left if l.days_left is not None else 9999))
