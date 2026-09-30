from __future__ import annotations

import csv
import html
import json
from datetime import date
from pathlib import Path

from .models import Lead

COLS = ["tier", "score", "stage", "source", "title", "buyer", "province", "notice_type", "published", "closing",
        "days_left", "est_value", "contract_start", "contract_end", "contact_name", "contact_email",
        "contact_phone", "url", "why"]


def _row(l: Lead) -> dict:
    o = l.opp
    return {"tier": l.tier, "score": l.score, "stage": l.stage, "source": o.source, "title": o.title, "buyer": o.buyer,
            "province": o.province, "notice_type": o.notice_type, "published": o.published or "",
            "closing": o.closing.strftime("%Y-%m-%d %H:%M") if o.closing else "",
            "days_left": "" if l.days_left is None else l.days_left,
            "est_value": "" if l.est_value is None else int(l.est_value),
            "contract_start": o.contract_start or "", "contract_end": o.contract_end or "",
            "contact_name": o.contact_name, "contact_email": o.contact_email,
            "contact_phone": o.contact_phone, "url": o.url, "why": "; ".join(l.reasons)}


def write_csv(leads: list[Lead], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(_row(l) for l in leads)


def write_json(leads: list[Lead], path: Path) -> None:
    path.write_text(json.dumps([_row(l) for l in leads], indent=2, default=str), encoding="utf-8")


def write_html(leads: list[Lead], path: Path) -> None:
    e = html.escape
    rows = []
    for l in leads:
        r = _row(l)
        contact = e(r["contact_name"])
        if r["contact_email"]:
            contact += f' &lt;<a href="mailto:{e(r["contact_email"])}">{e(r["contact_email"])}</a>&gt;'
        rows.append(
            f'<tr class="t{r["tier"]}"><td>{r["tier"]}</td><td>{r["score"]}</td><td>{e(r["stage"])}</td>'
            f'<td><a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["title"])}</a>'
            f'<div class="why">{e(r["why"])}</div></td><td>{e(r["buyer"])}<br><small>{e(r["province"])} · {e(r["source"])}</small></td>'
            f'<td>{e(r["notice_type"])}</td><td>{r["closing"][:10]}</td><td>{r["days_left"]}</td>'
            f'<td>{"" if r["est_value"] == "" else "$" + format(r["est_value"], ",")}</td><td>{contact}</td></tr>')
    path.write_text(f"""<!doctype html><meta charset="utf-8"><title>Training leads {date.today()}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font:14px system-ui;margin:1.5rem;color:#1a1a1a}}table{{border-collapse:collapse;width:100%}}
th,td{{padding:.45rem .6rem;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}}
th{{cursor:pointer;background:#f4f4f4;position:sticky;top:0}}.why{{color:#666;font-size:12px;margin-top:2px}}
tr.tA td:first-child{{background:#2e7d32;color:#fff;font-weight:700}}tr.tB td:first-child{{background:#f9a825;font-weight:700}}
tr.tC td:first-child{{background:#bbb;font-weight:700}}input{{padding:.4rem;width:20rem;margin-bottom:1rem}}
@media(prefers-color-scheme:dark){{body{{background:#161616;color:#eee}}th{{background:#222}}td,th{{border-color:#333}}a{{color:#8ab4f8}}}}</style>
<h1>Public sector training leads</h1><p>{len(leads)} leads · generated {date.today()}. Click headers to sort.</p>
<input id=q placeholder="Filter…" oninput="f()"><table id=t><thead><tr><th>Tier<th>Score<th>Stage<th>Opportunity
<th>Buyer<th>Notice type<th>Closes<th>Days<th>Est. value<th>Contact</tr></thead><tbody>{''.join(rows)}</tbody></table>
<script>const T=document.getElementById('t').tBodies[0];function f(){{const q=document.getElementById('q').value.toLowerCase();
for(const r of T.rows)r.hidden=!r.textContent.toLowerCase().includes(q)}}
document.querySelectorAll('th').forEach((h,i)=>h.onclick=()=>{{const d=h.dir=h.dir=='a'?'d':'a';
[...T.rows].sort((a,b)=>{{let x=a.cells[i].textContent,y=b.cells[i].textContent,n=parseFloat(x.replace(/[$,]/g,'')),m=parseFloat(y.replace(/[$,]/g,''));
let c=isNaN(n)||isNaN(m)?x.localeCompare(y):n-m;return d=='a'?c:-c}}).forEach(r=>T.appendChild(r))}})</script>""",
        encoding="utf-8")
