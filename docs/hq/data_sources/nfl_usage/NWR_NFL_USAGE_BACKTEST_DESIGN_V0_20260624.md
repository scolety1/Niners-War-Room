# NFL Usage Backtest Design V0

## Purpose

Define how NFL usage evidence could later prove it is safe and additive before display-only or model-candidate promotion.

## Design

- Target outcomes: future role stability, future touches, future targets, future snap share, and existing NWR outcome labels where point-in-time safe.
- Validation: walk-forward seasons only.
- Feature cutoff: only fields available before the prediction timestamp.
- Leakage checks: block final-season aggregates, market/rank/projection fields, same-season hindsight, and post-cutoff updates.
- Baseline comparison: compare against current approved model or display baseline without new usage fields.
- Ablations: core stats only, snaps only, red-zone only, advanced context only, all usage fields.
- Stratification: QB/RB/WR/TE, rookie/veteran, injury/role status, low/high snap samples.
- Pass thresholds: improved calibration or ranking utility with no unstable subgroup degradation.
- Rollback: remove any non-additive field and quarantine schema/source if drift appears.
