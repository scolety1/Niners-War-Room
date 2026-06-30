# Binding Guardrail Report

## Scope

This lane created a docs/CSV identity binding packet only under:

`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`

## Guardrail Results

- App pages changed: no
- Rankings behavior changed: no
- Player Compare behavior changed: no
- Trading Lab behavior changed: no
- Development Lab behavior changed: no
- Draft Room behavior changed: no
- Outcome probabilities changed: no
- Model logic changed: no
- Rank logic changed: no
- Source-truth logic changed: no
- Latest pointers changed: no
- Frozen board or protected artifacts changed: no
- Player context artifact rebuilt: no
- Non-approved rows bound: no
- `ff_rankings` used: no
- DynastyProcess IDs used as binding evidence: no
- Raw/shared/cache/local_exports/secrets tracked: no

## Conservative Flags

Every binding row keeps:

- `review_only=true`
- `display_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `hidden_sort_allowed=false`
- `trade_value_allowed=false`
- `pick_value_allowed=false`

## Binding Counts

- Approved overlay rows: 43
- Bound review-only rows: 41
- Needs more information rows: 2
- Ambiguous blocked rows: 0
- Non-approved overlay rows left unbound: 11

## Remaining Blockers

Rows in `unbound_or_ambiguous_identity_rows.csv` remain gated until a later human/Data Hygiene lane provides stronger NWR/Sleeper binding evidence.
