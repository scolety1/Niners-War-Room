# Model v4 Regeneration Stop Conditions

Regeneration must stop immediately if any of these conditions occur:

- Required source artifacts are missing.
- Source hash cannot be recorded.
- Decision-date safety cannot be proven.
- Current/future data is required.
- Identity joins are name-only, duplicated, ambiguous, or unstable.
- Missingness cannot distinguish true zero from unknown.
- Source gate is blocked.
- Raw/proprietary/non-admitted data is required.
- Route/YPRR/TPRR, return scoring, or shadow metrics are needed.
- Output would imply production/model-use.
- Output would write to canonical `local_exports`.
- Output would change app, ranking, model, runtime, source-gate, or board artifact behavior.
- Regeneration code would tune weights, run benchmarks, run Formula Gauntlet, or select formula winners.

If stopped, the lane must produce a blocker report and no regenerated receipt file.
