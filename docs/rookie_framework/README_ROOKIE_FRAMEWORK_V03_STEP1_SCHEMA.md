# Rookie Framework v0.3 Step 1 Schema README

## What Was Created

Step 1 creates a tracked rookie-only schema checkpoint under `docs/rookie_framework/`:

- `ROOKIE_FRAMEWORK_V03_SCHEMA_CONTRACT_20260613.md`
- `ROOKIE_FRAMEWORK_V03_FIELD_DICTIONARY_20260613.csv`
- `ROOKIE_FRAMEWORK_V03_PROMOTION_GATES_20260613.md`
- `README_ROOKIE_FRAMEWORK_V03_STEP1_SCHEMA.md`

These files define allowed evidence statuses, allowed source types, prohibited private-value inputs, pick-zone labels, tag categories, manual-review rules, hard-cap versus soft-flag behavior, field-level handling, and future promotion gates.

## Why It Is Safe

This checkpoint is documentation-only and rookie-only. It does not modify rankings, private scores, production formulas, Streamlit/app files, outcome-column files, veteran outcome heads, `data/`, or `local_exports/`.

The schema preserves the current v0.3 stance:

- v0.3 is review-only.
- Source caveats remain visible.
- Soft flags do not open pick zones.
- Manual scouting/prose is not converted into numeric grades.
- Market, ranking, projection, ADP, consensus, trade-value, draft-kit, prior draft history, RotoWire ranking/projection, and legacy `private_score` inputs remain prohibited as private-value evidence.
- Rookie probabilities, bands, and app-readable outcome columns remain blocked.
- Rookies are not forced through veteran outcome heads.

## What It Enables Next

This checkpoint enables a future Rookie Framework Step 2 to build a source-safe review-board export from v0.3 candidate artifacts. That future export should carry evidence statuses, source types, provenance, manual-review reasons, hard caps, soft flags, remaining gaps, and review-only pick-zone labels.

Step 1 also gives future audits a stable schema to validate against before any shadow export or promotion discussion.

## What It Does Not Enable Yet

This checkpoint does not enable:

- final rookie rankings;
- production scoring;
- private-score replacement;
- active Rankings hash changes;
- app or Streamlit display;
- rookie probabilities;
- rookie probability bands;
- app-readable rookie outcome columns;
- outcome-column files;
- veteran outcome-head usage;
- promoted model artifacts;
- commits to `data/` or `local_exports/`.

## Recommended Step 2

Create a rookie review-board export from v0.3 candidate artifacts, still review-only, no rankings/probabilities/app promotion.

Step 2 should remain in rookie-owned zones and should stop immediately if it detects market/rank/projection contamination, unexpected ranking/private-score changes, row-count breaks, unresolved premium-pick source conflicts, probability/band creation, or any attempt to route rookies through veteran outcome heads.
