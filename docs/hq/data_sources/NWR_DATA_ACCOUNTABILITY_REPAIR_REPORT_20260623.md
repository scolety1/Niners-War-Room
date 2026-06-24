# NWR Data Accountability Repair Report - 20260623

## Final Verdict
GREEN

## What Was Fixed
- Built Sleeper current free-agent verification against the LVE PDF page 3 pool.
- Built Sleeper status/injury metadata warning context with explicit partial-source language.
- Built player ID coverage audit and manual review queue across key surfaces.
- Preserved K/DST hidden-by-default behavior in the audit.
- Preserved `Not enough information` for missing Outcome/status/injury/ID evidence.

## Data Health Snapshot
- Frozen board rows: 66 / expected 66
- Pinned hash: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- Source freshness status: GREEN_RUNTIME_PULL at 2026-06-24T02:31:00+00:00
- PDF rows: 77
- PDF include-default rows: 63
- PDF K/DST hidden default rows: 14
- Sleeper/PDF audit categories: `{'PDF_MATCHED_BUT_ROSTERED_CONFLICT': 9, 'PDF_MATCHED_SLEEPER_FA': 54, 'PDF_KDST_HIDDEN_DEFAULT': 14, 'SLEEPER_FA_NOT_IN_PDF': 3909}`
- Status warning counts: `{'clean': 114, 'injury/status review': 16, 'missing status metadata': 8, 'team/status mismatch': 5}`
- Missing Sleeper age rows in status context: 13
- Missing team rows in status context: 0
- Identity confidence counts: `{'HIGH': 1065, 'MEDIUM': 52, 'LOW': 22}`
- Manual identity review rows: 74
- Outcome support rows: 12
- Outcome `Not enough information` rows: 54

## Remaining Caveats
- Sleeper status flags are not full injury/news analysis.
- Sleeper unrostered rows not present in LVE PDF page 3 are verifier/update candidates only.
- DynastyProcess/ADP/vendor/market fields remain display-only and cannot drive NWR value.
- Complete historical trade history and verified historical dropped-veteran truth remain research gaps.

## Outputs
- `docs/hq/data_sources/current_context/sleeper_pdf_free_agent_pool_audit_v1.csv`
- `docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv`
- `docs/hq/data_sources/current_context/sleeper_player_status_context_schema_v1.json`
- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
- `docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv`

## Guardrail Confirmation
No frozen board, final_board_rank, Dynasty Rank, latest_candidate, latest_approved, pinned snapshot, model logic, market input, or raw shared-data artifact is intentionally mutated by this lane.
