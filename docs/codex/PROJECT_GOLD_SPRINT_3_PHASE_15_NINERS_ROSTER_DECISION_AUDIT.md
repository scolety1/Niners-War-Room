# Project Gold Sprint 3 / Phase 15: Niners Roster Decision Audit

Date: 2026-05-14

## Result

Audited all 24 Niners roster players from the active pack:

`local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

The roster-decision gate is passing:

- Roster Decisions: `Roster Decisions Ready`
- Draft Ready: `Draft Pool Needs Data`
- Final Money Decisions: `Needs Data`
- Blocked checklist rows: `0`
- Review checklist rows: `0`

This means pre-declaration roster review can be inspected. It does not mean draft/final money decisions are ready.

## Classification Summary

| classification | count |
|---|---:|
| core hold | 1 |
| forced-release candidate | 1 |
| bubble | 7 |
| shop | 11 |
| cut/release candidate | 4 |

## Cross-Cutting Caveats

These caveats apply broadly and should be considered before acting:

- All 24 roster players currently have missing trade-market references. This affects trade context, not private Model Value.
- 20 players rely on local baseline projection only. This is visible in receipts and does not count as independent projection evidence.
- 4 players are low-confidence year-one bridge assets with missing NFL/LVE history and missing independent projections.
- The forced-release candidate is a rule-layer result, not a pure football cut.

## Player Audit

| player | pos | lifecycle | league rank | top-five rule | classification | Model Value | Keep Priority | Cut Risk | confidence | why questionable |
|---|---|---|---:|---|---|---:|---:|---:|---:|---|
| Brian Thomas | WR | Year-Two NFL Bridge | 66 | Top-five protected slot | core hold | 75.81 | 72.49 | 22.97 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Luther Burden | WR | Year-One NFL Bridge | 56 | Required top-five release slot | forced-release candidate | 49.48 | 37.79 | 55.46 | 36.0 | low confidence; missing NFL/LVE history; missing independent projection; missing trade market reference; year-one bridge relies on prospect prior more than NFL evidence; forced-release rule candidate, not a pure football cut |
| Oronde Gadsden | TE | Year-One NFL Bridge | 104 | Not in league-rank top five | bubble | 26.26 | 11.62 | 65.19 | 38.5 | low confidence; missing NFL/LVE history; missing independent projection; missing trade market reference; missing role/participation proxy; year-one bridge relies on prospect prior more than NFL evidence |
| Jayden Higgins | WR | Year-One NFL Bridge | 113 | Not in league-rank top five | bubble | 49.75 | 38.11 | 55.26 | 36.0 | low confidence; missing NFL/LVE history; missing independent projection; missing trade market reference; year-one bridge relies on prospect prior more than NFL evidence |
| Kaleb Johnson | RB | Year-One NFL Bridge | 131 | Not in league-rank top five | bubble | 53.16 | 48.20 | 51.88 | 36.0 | low confidence; missing NFL/LVE history; missing independent projection; missing trade market reference; year-one bridge relies on prospect prior more than NFL evidence |
| Jakobi Meyers | WR | Established Veteran | 95 | Not in league-rank top five | bubble | 65.50 | 62.65 | 34.04 | 66.5 | medium confidence; local baseline projection only; missing trade market reference; mild age decline |
| De'Von Achane | RB | Year-Three NFL Bridge | 10 | Top-five protected slot | bubble | 66.14 | 62.94 | 33.00 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Jerry Jeudy | WR | Established Veteran | 152 | Not in league-rank top five | bubble | 64.33 | 61.92 | 32.61 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |
| Brandon Aiyuk | WR | Established Veteran | 98 | Not in league-rank top five | bubble | 67.20 | 64.28 | 28.83 | 66.5 | medium confidence; local baseline projection only; missing trade market reference; mild age decline |
| Luke McCaffrey | WR | Year-Two NFL Bridge | 263 | Not in league-rank top five | shop | 36.28 | 29.96 | 54.69 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Ricky Pearsall | WR | Year-Two NFL Bridge | 91 | Not in league-rank top five | shop | 49.94 | 42.03 | 54.68 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Jalen Coker | WR | Year-Two NFL Bridge | 147 | Not in league-rank top five | shop | 44.44 | 38.16 | 54.43 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Quentin Johnston | WR | Year-Three NFL Bridge | 94 | Not in league-rank top five | shop | 50.53 | 43.55 | 48.43 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Lamar Jackson | QB | Established Veteran | 31 | Top-five protected slot | shop | 54.68 | 41.09 | 46.84 | 68.5 | medium confidence; local baseline projection only; missing trade market reference; top-five rule protects player but model bucket is shop |
| David Montgomery | RB | Established Veteran | 97 | Not in league-rank top five | shop | 53.88 | 50.54 | 46.10 | 66.5 | medium confidence; local baseline projection only; missing trade market reference; age/dropoff risk |
| Wan'Dale Robinson | WR | Established Veteran | 118 | Not in league-rank top five | shop | 55.43 | 52.76 | 45.80 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |
| Romeo Doubs | WR | Established Veteran | 172 | Not in league-rank top five | shop | 55.17 | 48.36 | 43.51 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |
| Chase Brown | RB | Year-Three NFL Bridge | 35 | Top-five protected slot | shop | 54.38 | 52.46 | 42.03 | 66.5 | medium confidence; local baseline projection only; missing trade market reference; mild age decline; top-five rule protects player but model bucket is shop |
| Xavier Worthy | WR | Year-Two NFL Bridge | 133 | Not in league-rank top five | shop | 62.08 | 53.86 | 41.72 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Devin Singletary | RB | Established Veteran | 268 | Not in league-rank top five | shop | 53.47 | 52.21 | 41.12 | 66.5 | medium confidence; local baseline projection only; missing trade market reference; age/dropoff risk |
| Brenton Strange | TE | Year-Three NFL Bridge | 125 | Not in league-rank top five | cut/release candidate | 27.56 | 15.70 | 66.31 | 66.5 | medium confidence; local baseline projection only; missing trade market reference |
| Daniel Jones | QB | Established Veteran | 246 | Not in league-rank top five | cut/release candidate | 34.91 | 18.54 | 58.38 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |
| T.J. Hockenson | TE | Established Veteran | 206 | Not in league-rank top five | cut/release candidate | 43.46 | 30.66 | 57.78 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |
| Jake Ferguson | TE | Established Veteran | 109 | Not in league-rank top five | cut/release candidate | 38.34 | 26.35 | 57.08 | 68.5 | medium confidence; local baseline projection only; missing trade market reference |

## Notes On Questionable Rows

- `Luther Burden` is the current forced-release candidate because he is the least painful league-rank top-five release under the active model. This is a top-five rule result. It should be reviewed carefully because he is a year-one bridge asset with low confidence and no NFL/LVE history.
- `Lamar Jackson` and `Chase Brown` are top-five protected by the rule but still fall into a shop-style model bucket. That is not a forced-release instruction; it means the private model does not treat them as high-priority holds under this exact 1QB/no-PPR/first-down format. Review receipts before acting.
- `Kaleb Johnson`, `Jayden Higgins`, `Oronde Gadsden`, and `Luther Burden` all depend heavily on young-player bridge assumptions because they lack NFL/LVE history.
- The TE rows are heavily suppressed by the no-TE-premium format and route/target dependency.

## Exports

Audit CSV:

`local_exports/model_audits/sprint3_phase15_niners_roster_decision_audit_20260514/niners_roster_decision_audit.csv`

Manifest:

`local_exports/model_audits/sprint3_phase15_niners_roster_decision_audit_20260514/manifest.json`

## Patch Decision

No player score, formula, identity, or normalization changes were made in this phase. The audit did not find a supported data/identity/normalization bug. The questionable rows are documented for manual review rather than patched blindly.
