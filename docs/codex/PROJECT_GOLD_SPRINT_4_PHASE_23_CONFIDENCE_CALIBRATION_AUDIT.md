# Project Gold Sprint 4 / Phase 23: Confidence Calibration Audit

## Purpose

Confidence should describe source quality, not player quality. A strong player can still carry review-only confidence when the model is relying on proxy role data, stale production, local-baseline projections, missing injury detail, or identity warnings.

## New Audit Export

Run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\export_confidence_calibration_audit.py
```

The export writes a timestamped folder under `local_exports/model_audits/` with:

- `confidence_calibration_audit_rows.csv`
- `confidence_calibration_summary.csv`
- `confidence_calibration_explanations.csv`
- `manifest.json`

## Audit Logic

The audit compares current visible model confidence against rebuilt source-quality confidence. It checks:

- production coverage
- role/usage coverage
- projection source status
- injury status
- age/bio source
- identity confidence
- outlier status

The row is flagged when the visible confidence tier is materially higher than the source-quality tier supports. This catches cases where a player looks "usable" even though the underlying data says "review before action."

## Formula Safety Patch

The stats-first formula now caps confidence when core source quality is weak:

- missing scoring history: capped below usable confidence
- missing role/usage: capped below usable confidence
- proxy/stale role or production inputs: capped below usable confidence
- local-baseline projection: capped at limited confidence only
- missing injury detail: capped only if the row is otherwise claiming high certainty

This does not change private/model value. It only prevents fake certainty.

## Current Policy

Rankings remain review-only unless the decision gates pass. Missing optional data should not bury a player, but it also should not allow a decision-ready confidence claim.
