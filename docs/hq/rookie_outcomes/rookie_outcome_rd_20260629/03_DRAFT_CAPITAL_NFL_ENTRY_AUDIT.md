# Draft Capital And NFL Entry Audit - 2026-06-29

## Verdict

Draft capital is partially present as prior prototype/review context, but it is not currently sufficient for an active rookie outcome build.

Primary blocker: no approved tracked draft-capital artifact covering both historical and current rookie classes.

## Machine-Readable Output

Created:

`docs/hq/rookie_outcomes/rookie_outcome_rd_20260629/rookie_draft_capital_availability_matrix.csv`

Rows: 6 source/status rows.

## Availability Summary

| Source | Status | Notes |
|---|---|---|
| CFBD identity link registry DRAFT | partial | Identity candidates only; no human approval. |
| 2026 draft capital snapshot doc | partial_local_only | Documents 257-row local snapshot, but processed CSV lives under `local_exports`. |
| Historical rookie replay templates | missing | Headers exist, production rows do not. |
| Historical rookie replay sample data | sample_only | Useful for tests, not source truth. |
| Model v4 rookie outcome labels service | blocked_policy | Depends on local_exports and RotoWire-derived stats. |
| fact_rookie_draftables template | missing | Empty template. |

## Fields Needed For Future Build

Required fields:

- NFL draft year
- NFL draft round
- NFL overall pick
- NFL team drafted by
- undrafted free agent status
- rookie class year
- age at draft
- position at draft
- early declare or class year, if available

## Field Status

| Field | Current Status | Blocker |
|---|---|---|
| NFL draft year | partial | 2026 documented locally; historical production-ready artifact missing. |
| NFL draft round | partial | 2026 local-only/prototype; historical approved source missing. |
| NFL overall pick | partial | 2026 documented; historical approved source missing. |
| NFL team drafted by | partial | available in some prototype/sample contexts only. |
| Undrafted free agent status | missing | no approved structured artifact found. |
| Rookie class year | partial | implied in samples/templates; not approved across universe. |
| Age at draft | partial | age gaps/conflicts remain unresolved for rookies/prospects. |
| Position at draft | partial | present in some rows; identity and position timeline not approved. |
| Early declare / class year | missing | no approved structured source found. |

## Safe Use Now

Draft capital can be discussed as a future required feature family.

It cannot be used now as:

- rookie outcome feature
- training truth
- Rankings column
- hidden sort
- trade value
- pick value

## Required Next Step

Create an approved review-only draft capital artifact that:

- is tracked under `docs/` or another approved artifact root
- excludes raw/local cache paths
- includes source lineage
- is identity-gated
- covers historical classes and current rookie/prospect rows
- keeps `model_use_allowed=false` until a later promotion gate
