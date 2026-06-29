# Draft-Class / GSIS Bridge Inventory - 2026-06-30

## Current Master

- Base HEAD: `5dc578d9c8feaa02b49f8db9700999f651158500`
- Branch: `work/historical-rookie-draft-class-gsis-bridge-v1-20260630`

## Prior Rookie Gates

- Gate A: `GREEN_REVIEW_ONLY_IDENTITY_APPROVAL`
- Gate B: `PARTIAL_DRAFT_CAPITAL_REVIEW_ARTIFACT`
- Gate C: `BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE`

## Sources Inventoried

- Gate A CFBD identity approval artifact: current/future review-only identity context.
- Gate B draft capital artifact: partial current 2026 review-only draft context.
- CFBD identity/link registries: review-only, not source truth.
- NWR player ID maps: useful for current players, not sufficient for historical GSIS bridge.
- Sleeper/NWR IDs: not enough for historical player_stats labels by themselves.
- `nflreadpy` dependency approval: loaders are approved, but not installed in this runtime.
- nflverse draft-picks release CSV: public structured draft class plus GSIS/PFR IDs.
- Outcome V2 target labels under shared data: review-only factual NFL outcome labels.
- Old prototype/model files: reference only, not source-approved for labels.

## Sources Excluded

- Market, ADP, DynastyProcess, projections, vendor/RotoWire, Gmail, and scraping.
- CFBD as NFL outcome truth.
- App display gaps as negative labels.

## Generated Shared Outputs

- Bridge CSV: `C:\NWR_SHARED_DATA\rookie_outcomes\draft_class_gsis_bridge_v1\historical_rookie_draft_class_gsis_bridge_v1.csv`
- Manifest CSV: `C:\NWR_SHARED_DATA\rookie_outcomes\draft_class_gsis_bridge_v1\historical_rookie_draft_class_gsis_bridge_manifest_v1.csv`
- Coverage CSV: `C:\NWR_SHARED_DATA\rookie_outcomes\draft_class_gsis_bridge_v1\historical_rookie_draft_class_gsis_bridge_coverage_summary_v1.csv`
- Shared outputs are outside git and must remain untracked.

## Inventory Counts

- Bridge rows built: 1025
- Outcome V2 rows inspected: 7440
- Outcome V2 manifest rows inspected: 3
