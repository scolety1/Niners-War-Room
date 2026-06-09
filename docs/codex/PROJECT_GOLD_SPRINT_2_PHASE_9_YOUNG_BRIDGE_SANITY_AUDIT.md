# Project Gold Sprint 2 / Phase 9 Audit: Young Player Bridge Sanity

Date: 2026-05-14

## Scope

This audit checks whether year-one, year-two, and year-three NFL players are being valued as bridge assets rather than pure veterans.

Rankings remain review-only.

Audit artifacts were written to:

`local_exports/model_audits/sprint2_phase9_young_bridge_sanity_20260514`

Files:

- `young_bridge_sanity_all_rankings.csv`
- `young_bridge_sanity_young_players.csv`
- `young_bridge_sanity_top_young_assets.csv`
- `young_bridge_sanity_niners_young_players.csv`
- `young_bridge_sanity_flags.csv`
- `young_bridge_sanity_established_leaks.csv`
- `young_bridge_sanity_summary.csv`
- `manifest.json`

## Result

The young-player bridge is now visible and split by experience year.

Counts:

- Total active rows audited: 1,039
- Established veterans: 634
- Year-one NFL bridge: 145
- Year-two NFL bridge: 128
- Year-three NFL bridge: 132

No established veteran draft-capital leak was found.

## Flags

Flag counts:

- `nfl_evidence_missing`: 215
- `prior_too_dominant`: 145
- `established_veteran_draft_capital_leak`: 0

Interpretation:

- The `prior_too_dominant` flags are concentrated on year-one players. That is expected review behavior because incoming/first-year players have limited NFL evidence.
- The `nfl_evidence_missing` flags are not a formula bug. They identify players whose bridge value is still being carried by draft/prospect context more than real NFL production and role evidence.
- Established veterans are clean: draft capital is not contributing to established-veteran private value.

## Niners Young Players

Niners bridge rows:

| player | lifecycle | prior | bridge weight | NFL evidence | confidence | flags |
|---|---:|---:|---:|---:|---:|---|
| De'Von Achane | Year-Three NFL Bridge | 73.0 | 0.048 | 0.674 | 66.5 | none |
| Xavier Worthy | Year-Two NFL Bridge | 90.0 | 0.126 | 0.674 | 66.5 | none |
| Chase Brown | Year-Three NFL Bridge | 44.0 | 0.048 | 0.674 | 66.5 | none |
| Kaleb Johnson | Year-One NFL Bridge | 73.0 | 0.350 | 0.000 | 36.0 | nfl_evidence_missing; prior_too_dominant |
| Quentin Johnston | Year-Three NFL Bridge | 90.0 | 0.048 | 0.674 | 66.5 | none |
| Ricky Pearsall | Year-Two NFL Bridge | 90.0 | 0.126 | 0.674 | 66.5 | none |
| Jalen Coker | Year-Two NFL Bridge | 48.0 | 0.126 | 0.674 | 66.5 | none |
| Jayden Higgins | Year-One NFL Bridge | 82.0 | 0.350 | 0.000 | 36.0 | nfl_evidence_missing; prior_too_dominant |
| Luke McCaffrey | Year-Two NFL Bridge | 72.0 | 0.126 | 0.674 | 66.5 | none |
| Brenton Strange | Year-Three NFL Bridge | 77.0 | 0.048 | 0.674 | 66.5 | none |

Kaleb Johnson and Jayden Higgins are correctly flagged as year-one bridge assets with missing NFL evidence. That means their draft/prospect prior is visible, but not trustworthy enough to use as certainty.

## Patch Decision

No lifecycle, bridge, or normalization bug was found during this audit.

No formula weights were changed.

The named sanity fixture coverage was already present for:

- Brian Thomas Jr. vs Luther Burden
- Chase Brown vs Luther Burden
- Kaleb Johnson vs older fragile RB
- Jayden Higgins vs low-upside veteran WR
- high-capital limited-production WR
- low-capital limited-production WR
- young RB with uncertain role
- established veteran over limited young profile

The Phase 9 rebuild also added regression coverage for year-specific lifecycle labels and NFL evidence receipt display.

## Remaining Model Risk

The bridge layer is now behaving transparently. The remaining risk is data quality:

- year-one players need real NFL evidence as the season develops
- role/usage truth is still a major gap
- projection quality remains review-only
- rankings should stay review-only until named sanity fixtures and cross-position balance are audited against receipts

