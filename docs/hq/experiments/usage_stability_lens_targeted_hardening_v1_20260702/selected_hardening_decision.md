# Selected Hardening Decision

Decision label: `KEEP_AS_USAGE_LENS_ONLY_NO_RANK_VARIANT`

Selected review posture: `usage_lens_with_cornerstone_warning_flags`

No rank-changing hardening variant is selected for production, shadow rank replacement, app preview, hidden sort, or recommendations.

## Rationale

The warning-flag posture best satisfies the targeted mission:

- It preserves the lens's historical usefulness.
- It does not materially degrade holdout/startable metrics because it does not alter ranks.
- It flags CeeDee Lamb, Justin Jefferson, and Brock Bowers as cornerstone stability review risks.
- It does not blindly boost Malik Nabers or Garrett Wilson.
- It keeps injury/context caution in human review.
- It is interpretable.
- It uses no player-name formula exceptions.
- It uses no market data as source truth.

## Selection Discipline

The variants were fixed before holdout review. Holdout was not used to choose thresholds, tune weights, or run a formula search.
