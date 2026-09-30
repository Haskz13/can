# leadgen — Canadian public sector training lead generator

Pulls live tender notices from the [CanadaBuys open-data feeds](https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/open-data),
keeps only training/learning opportunities that are **still actionable**, and ranks them by likely deal value.

```bash
python -m leadgen                       # fetch + score, writes output/leads.{csv,json,html}
python -m leadgen --focus leadership --focus cybersecurity
python -m leadgen --offline             # reuse cached feeds in data/
cp config.example.toml config.toml      # tune windows, topics, provinces, buyers
python -m pytest
```

No dependencies beyond Python 3.11.

## How a lead is scored (0–100)
- **Relevance (50%)** – EN/FR training keywords (title counts double), UNSPSC 86xx and GSIN "U" codes, your `focus` topics; penalises false positives (training centres, simulators, horses, construction).
- **Value (25%)** – the federal feed has no dollar amounts, so value is inferred: `$` figures in the text, contract term, standing offers / supply arrangements, multi-year/option years, cohort or headcount hints.
- **Timing (25%)** – days until close (bids closing in < `min_days_left` are dropped), freshness of the posting. RFIs, ACANs, ITQs and supply-arrangement notices are flagged **early signal** and stay live longer: the best time to contact the buyer is before the RFP.

Tier A ≥ 70, B ≥ 55, C otherwise.

## Limits / next steps
- Only CanadaBuys today. Provincial and municipal portals (MERX, BC Bid, SEAO, Alberta Purchasing Connection, Ontario Tenders Portal) plug in as new modules in `leadgen/sources/` returning `Opportunity` objects.
- Award notices / contract history (incumbent, value, expiry → re-compete forecasting) would add real dollar values.

## Provincial and multi-portal coverage
`python -m leadgen --portals` lists every federal, provincial, territorial and municipal portal and how it is covered.

| Coverage | Portals |
|---|---|
| **Automatic** | CanadaBuys (federal), SEAO (Québec, incl. municipalities, school boards, health networks) |
| **Via CSV import** | Ontario, BC Bid, Alberta, Saskatchewan, Manitoba, NB, NS, PEI, NL, territories, plus MERX, Biddingo, Bids&Tenders, BIDS Alert and Tenders On Time |

The other provinces publish no open tender feed (Ontario and BC sit behind JavaScript/browser checks, NL and Manitoba
post on MERX, and PEI/Yukon block automated access). leadgen does not try to bypass those protections.
Instead, set up a saved search (keywords like *training, formation, workshop, coaching, e-learning*, UNSPSC 8610xxxx) on
each portal or aggregator, export the results to CSV, and drop the files in `imports/`. Columns are matched by name
(`Title`, `Organization`, `Closing Date`, …); add aliases under `[import_columns]` in `config.toml` if an export uses others.
Imported rows are scored, de-duplicated against the automatic feeds, and ranked together.

Quebec reads ~7 weekly files (~18 MB each) on first run; later runs only refresh the current week. Use `--sources canadabuys` for a fast federal-only run.
