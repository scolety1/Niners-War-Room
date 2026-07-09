# Formula Gauntlet Data Hygiene Dependencies

Formula Gauntlet cannot run safely until Data Hygiene clears the data below.

## Label Dependencies

- Historical NWR scoring labels must be source-traced.
- First-down scoring treatment must be confirmed.
- 2025 reconciliation caveats must be carried forward.
- Position labels must exist for QB/RB/WR/TE.
- Startable labels must match the NWR league format.

## Identity Dependencies

- Canonical player ID coverage by season and position.
- No name-only joins.
- Collision and conflict rows flagged.
- PFR, NFLVerse, NGS, CFBD, and other bridges classified by use gate.
- Sparse-history and rookie players handled without forced current identity assumptions.

## Source / Use Gate Dependencies

Every input family must be classified as one of:

- model-use
- review-only
- display-only
- blocked
- identity-unsafe
- leakage-unsafe
- not enough information

Review-only data may support evidence review only. It cannot become production input.

## Missingness Dependencies

Data Hygiene must distinguish:

- true zero
- missing unknown
- unavailable source
- blocked source
- excluded row
- unsafe join

Formula Gauntlet cannot impute missingness as zero unless Data Hygiene explicitly approves the field and context.

## Leakage Dependencies

Future tournaments require:

- feature season and target season contract
- no current/future injuries, depth charts, ADP, market, rankings, or outcomes as historical inputs
- no target-season outcome labels as features
- retrieval/source timestamps when relevant
- as-of proof for each input family

## Exact Replay Dependencies

Exact Model v4 replay remains blocked until these season-by-season receipts exist or are replaced by a separate approved challenger-score contract:

- `checkpoint_review_score`
- `position_specific_review_score`
- lifecycle / age receipts
- role receipts
- confidence receipts
- WR/QB v2 candidate-overlay receipts
- exact rank and score outputs

## Current Data Hygiene Decision Needed

Data Hygiene should produce the next gate:

`DATA_HYGIENE_HISTORICAL_LABEL_IDENTITY_SOURCE_GATE_CLOSURE_V1`

That gate should say which inputs, labels, and slices are clean enough for future review-only tournament execution and which remain blocked.
