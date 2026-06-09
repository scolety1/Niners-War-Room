# Phase 10H Data Spine Checkpoint

Generated: 2026-05-17

Current traceability note: this checkpoint is preserved as historical
traceability and is superseded by Phase 10Q and Phase 10R. The old Phase 10G
matrix counts below are stale. Current formula-facing prospect state:

- Current prospects: 232
- Admitted prospect identities: 211
- Admitted prospect feature rows: 211
- Review-only prospects: 21
- `admitted_prospect_current_feature_matrix.csv` is the formula-facing current
  prospect matrix.
- Workout zero placeholders are repaired to missing values.
- CFB/college production and market share are prospect-prior evidence.
- CFBD is redistribution-limited but formula-admitted after validation.
- Phase 10N recheck passes with 14 checks, 0 issues.

Post-audit note: this checkpoint has been superseded by
`docs/model_v4/PHASE_10L_IDENTITY_SOURCE_REPAIR.md`. The external audit found
historical duplicate-name college evidence contamination, and Phase 10L repaired
the historical backtest leakage. Formula work should still wait until the
remaining current-prospect identity admission blocker is resolved.

## Goal

Decide whether the Model v4 data spine is ready for external audit before formula
design.

This phase did not rebuild formulas, calculate final rankings, promote app
rankings, alter My Team, alter War Board, or unlock readiness gates.

## Phase 10 Summary

### Raw Source Inventory

Phase 10A froze and inventoried the current source stack.

- Inventory file: `docs/model_v4/PHASE_10A_SOURCE_INVENTORY.csv`
- Inventoried files: 640
- Raw files hash-frozen: 502
- Processed/generated files recorded: 138
- Files allowed for private value after validation: 413
- Context/projection/market files excluded from private value: 24
- Issues logged: 397

Important remaining source-governance items:

- Third-party combine/pro-day files remain source-limited because local license
  files were not found.
- Several raw source families need family-level README or manifest notes before
  long-term formula admission.
- Market, ranking, ADP, mock, projection, and league-rank context are present
  only for comparison/audit lanes.

### Canonical First-Down Tables

Phase 10B canonicalized manually collected rushing and receiving first-down
exports for 2024 and 2025.

- Rushing canonical rows: 350
- Receiving canonical rows: 575
- Receipt rows: 925
- Coverage rows: 925
- Imported real data rows: 925
- Matched rows: 873
- Missing join rows: 23
- Ambiguous join rows: 29

Direct sourced first-down fields are labeled `imported_real_data`. Missing and
ambiguous joins remain review rows and were not silently joined.

### Canonical Return Tables And Scoring Contract

Phase 10C canonicalized 2024 and 2025 kick-return and punt-return exports and
patched the official LVE scoring constants.

- Canonical return rows: 302
- Receipt rows: 302
- Coverage rows: 302
- Missing join rows: 53
- Ambiguous join rows: 8
- Return yards found: 87,959
- Return TDs found: 34

Scoring constants now include:

- return yards = 1 per 30
- return TD = 4

Return production is labeled as small direct scoring evidence, not a major
talent signal or dynasty-weighting lever.

### Prospect Source Snapshot

Phase 10D copied the separate rookie/prospect package into the main Model v4
source system.

- Snapshot root:
  `local_exports/model_v4/prospect_sources/latest`
- Manifest:
  `docs/model_v4/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv`

Included source groups:

- CFBD college player/team/market-share/recruiting/draft tables
- RotoWire CFB stats, targets, team context, workouts, injuries, and depth
  context
- FantasyPros ADP and rookie ADP context
- Kaggle NFL Draft/big-board files
- Third-party combine/pro-day files

Market and rankings data remain context-only. Third-party combine/pro-day data
remains source-limited.

### Identity Crosswalk

Phase 10E built a review-only identity crosswalk across NFL/prospect sources.

- Source records: 287,557
- Canonical rows: 110,023
- Ready rows: 47,947
- Review rows: 12,614
- Unresolved rows: 7,610
- Ambiguous rows: 41,852
- Fuzzy joins used: False

The large ambiguous/unresolved counts are expected for a full multi-source
football universe. Phase 10G excludes or flags unsafe joins instead of silently
admitting them to formula-ready matrices.

### Source Trust Contract

Phase 10F made each source family's model lane explicit.

Classification counts:

- `scoring_evidence`: 5
- `derived_evidence`: 7
- `prospect_prior_evidence`: 6
- `context_only`: 7
- `market_context_only`: 6
- `source_limited`: 2
- `rejected`: 3

Confirmed rules:

- ADP, rankings, cheat sheets, mock drafts, and big boards cannot drive private
  football value.
- Imported projections and projected fantasy totals cannot drive private
  football value.
- League rank cannot drive Dynasty Asset Value.
- Market/liquidity remains separate from private football value.
- Missing data cannot become zero, average, or positive evidence.

### Evidence Matrices

Phase 10G created formula-ready evidence matrices without calculating final
rankings or formula scores.

Outputs:

- `local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/prospect_current_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/warning_matrix.csv`

Counts:

- NFL current player rows: 80
- Current prospect rows: 233
- Historical rookie backtest rows: 395
- Source coverage rows: 3,853
- Warning rows: 933

Hard QA counters:

- Duplicate entity rows: 0
- Market leakage violations: 0
- Fake-zero missing violations: 0
- Ambiguous join rows: 0
- Formula scores calculated: False
- Final rankings calculated: False

Phase 10G status: `ready_for_formula_design_review`.

## Remaining Blockers And Watch Items

These are not active app blockers because v4 remains review-only.

| Area | Status | Why It Matters | Next Action |
| --- | --- | --- | --- |
| Third-party combine/pro-day data | Source-limited | License/provenance was not found in local downloaded files. | Keep source-limited or replace with licensed RotoWire workout fields. |
| Broad identity crosswalk ambiguity | Tracked, not silently joined | Full universe includes many duplicate names and transfers. | Use Phase 10G matrix rows and coverage flags; resolve only names needed by formula/backtest. |
| First-down unmatched/ambiguous rows | Review | Some source rows lack enough identity context. | Resolve safe joins only when source-backed; do not fuzzy join. |
| Return unmatched/ambiguous rows | Review | Return evidence should be small and direct only. | Resolve safe joins only; keep return production from becoming a talent signal. |
| Raw source manifests | Governance cleanup | Some source families lack nearby README/MANIFEST notes. | Add family-level manifests before long-term source admission. |
| 933 matrix warnings | Expected review surface | Warnings expose missing/source-limited/context-only evidence. | Audit warning matrix before formula implementation. |

## Safety Confirmations

- Active rankings unchanged.
- Active My Team unchanged.
- Active War Board unchanged.
- No readiness gates unlocked.
- Formulas were not rebuilt.
- No app promotion occurred.
- Market, ADP, rankings, mock drafts, projections, league rank, and liquidity
  are excluded from private football value.
- Missing evidence remains missing/review, not zero-filled evidence.

## Decision

The data spine is ready for an external audit before formula work.

The evidence matrices are clean enough to audit because the hard safety checks
are green: no duplicate matrix entities, no market leakage, no fake-zero missing
values, and no ambiguous joins in the formula-ready rows.

The next phase should be an external data-spine audit before formula design. The
auditor should verify:

- source lanes match intended use
- first-down and return evidence are correctly labeled
- source-limited files are not treated as private value
- market/projection/ranking data is not leaking into factual or derived evidence
- warning and coverage rows are sufficient for formula work
- historical rookie backtest rows avoid post-draft/market leakage

If that audit passes, move to formula design using only Phase 10G formula-ready
lanes and receipts. If it fails, run a focused data/source repair pass before
formula work.

## Validation

Phase 10H validation was run after the checkpoint document was created:

- Static check: `ruff check app src scripts tests`
- Full test suite: `pytest`
