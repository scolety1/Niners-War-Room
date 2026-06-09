# Project Gold Sprint 2 / Phase 11 Audit: Market Contamination Check

Generated: 2026-05-14

## Verdict

Pass, with one important data-status note: the active preview currently has no real imported market data. Every active player row is classified as `missing_market`, so Model vs Market is unavailable rather than treated as a real edge.

Rankings remain review-only.

## What Changed During This Audit

- Regenerated the stats-first preview in review-only mode using the current market isolation policy.
- Mirrored the regenerated review-only preview into `local_exports/active_veteran_model_public_sources`.
- Added a repeatable audit exporter:
  - `scripts/export_market_contamination_audit.py`

The regeneration was needed because the active preview CSV still contained stale raw market-edge values from before the Phase 11 policy columns were physically written. The model/service policy already suppressed missing/default market edge, but the CSV now matches that policy too.

## Audit Packet

Latest audit packet:

`local_exports/model_audits/sprint2_phase11_market_contamination_20260514T192226`

Files:

- `manifest.json`
- `market_contamination_extreme_test.csv`
- `market_status_rows.csv`
- `market_status_summary.csv`

## Before/After Extreme Market Test

Rows tested: 1,039

The audit forced every normalized player row through two scores:

- low market: `market_liquidity = 0`
- high market: `market_liquidity = 100`
- both marked as `real_imported_market`

Results:

| check | result |
|---|---:|
| private/model value moved | 0 rows |
| keeper score moved | 0 rows |
| drop score moved | 0 rows |
| horizon score moved | 0 rows |
| trade value failed to move | 0 rows |
| Model vs Market failed to move | 0 rows |

This confirms market data cannot distort private/model ranking value.

## Missing/Default Market Check

Active preview rows by market status:

| status | rows |
|---|---:|
| `missing_market` | 1,039 |

Rows with unusable market edge leaks: 0

Missing/default market rows now render as unavailable for edge. They do not create fake positive or negative Model vs Market signals.

## Interpretation

The active app can still show private/model value rankings for review, but it should not present trade edge as meaningful until a real market source is imported. This is correct behavior for now.

Market data is isolated to:

- trade/liquidity value
- Model vs Market edge
- trade/market context surfaces

Market data does not affect:

- private/model value
- keeper score
- drop score
- horizon retention score

## Remaining Work

- Import a real market source later if we want usable Model vs Market trade edges.
- Keep missing market visible as an unavailable optional bucket, not a fatal roster-decision blocker.
- Keep rankings review-only until the broader sanity and audit gates pass.
