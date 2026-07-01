# Legacy Zero-Fill Replacement Or Fencing Report

## Verdict

YELLOW_IMPROVED_FENCED_NOT_FULLY_REPLACED

V2 replaced the highest-risk optional-source legacy zeros with nulls. It did not fully replace every Backtest V1 source-level zero-fill rule.

## Fenced

- Optional snap fields: `811` null-fenced rows.
- Optional air-yard/YAC fields: `663` null-fenced rows.
- Rows with at least one optional source fence: `1,371`.

## Still Requires V3 Review

Role/stat absence rules for core seasonal facts remain inherited from the source builder. V2 documents them and keeps all outputs review-only.
