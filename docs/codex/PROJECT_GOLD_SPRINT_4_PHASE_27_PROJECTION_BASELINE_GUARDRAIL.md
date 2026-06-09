# Project Gold Sprint 4 / Phase 27: Projection Baseline Guardrail

## Summary

Phase 27 hardens the rule that `local_baseline_projection` is context only. It can keep projection-related rows visible for audit, but it cannot masquerade as an independent forecast or create decision-ready confidence by itself.

## Guardrails Confirmed

- `expected_lve_points_score` stays neutral at `50.0` when the projection source is `local_baseline_projection`.
- `lve_projection_value` receipts now prioritize the local-baseline warning over other missing-data text when a local baseline projection row exists.
- `_confidence` only uses projection confidence from `independent_projection`; local baseline rows contribute neutral projection confidence.
- `_missing_data_penalty` keeps a penalty for non-independent projection rows.
- Warning translation now says: `projection is a local baseline, not forecast`.

## UI Visibility

The stronger phrase appears in warning translations and in the source coverage captions on:

- War Board advanced source coverage audit
- Model Lab source coverage audit

## Tests

Focused tests passed:

```text
32 passed
```

Covered areas:

- Local baseline projection cannot fill expected points.
- Local baseline projection alone cannot create decision-ready confidence.
- Warning text uses `local baseline, not forecast`.
- Source coverage behavior remains intact.

## Notes

No paid projection data was added. No model formula weights were tuned. Rankings and readiness behavior remain gated by the existing review-only / calibration system.
