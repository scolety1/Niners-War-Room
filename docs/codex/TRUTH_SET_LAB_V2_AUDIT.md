# Truth Set Lab v2 Audit

Status: review-only. No model formulas, active rankings, or gates changed.

## Files

- v2 preview folder: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_lab_v2_preview_20260515T045827`
- Audit groups: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v2\reports\truth_set_v2_audit_groups.csv`
- Major movement: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v2\reports\truth_set_v2_audit_major_movements.csv`
- Suspicious rankings: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v2\reports\truth_set_v2_audit_suspicious_rankings.csv`

## Summary

- Truth-set players: 40
- Audit group rows: 53
- Major movement rows: 0
- Suspicious rows: 88
- Production import status: `rejected`
- Role/usage import status: `rejected`
- Projection import status: `safe_after_derivation_with_rejections`

## Verdict

Truth Set Lab v2 improves auditability, not decision trust. Projection recompute and young-prior gap fills are stable, but production and role/usage remain rejected. Because those are the core evidence buckets, there is not enough clean signal to make formula conclusions yet.

## Import Status

- projections / raw stat columns: `safe_after_derivation` (can_import_after_recompute)
- projections / supplied fantasy points: `rejected` (do_not_use)
- projections / first-down estimates: `preview_only` (needs_manual_review)
- young_player_prior / draft capital prior: `safe_after_derivation` (can_import_after_recompute)
- production / production stat columns: `rejected` (needs_reexport)
- role_usage / route/workload usage fields: `rejected` (needs_reexport)
- injury / sourced injury context: `review_only` (can_import_as_context)
- market / trade liquidity: `trade_context_only` (can_import_as_context)

## Movement Classification

No major v1-to-v2 movement was found under the current thresholds. That means the v2 rerun did not destabilize rankings, but it also did not solve the trust problem because corrected production and role/usage did not enter.

## Remaining Suspicious Rows

- Wan'Dale Robinson: projection_team_mismatch (medium)
- Wan'Dale Robinson: role_usage_rejected (medium)
- Wan'Dale Robinson: production_rejected (medium)
- Jahmyr Gibbs: role_usage_rejected (medium)
- Jahmyr Gibbs: production_rejected (medium)
- Xavier Worthy: role_usage_rejected (medium)
- Xavier Worthy: production_rejected (medium)
- Christian McCaffrey: role_usage_rejected (medium)
- Christian McCaffrey: production_rejected (medium)
- Ricky Pearsall: role_usage_rejected (medium)
- Ricky Pearsall: production_rejected (medium)
- Chase Brown: role_usage_rejected (medium)

## Recommended Next Action

Do not tune formulas from this v2 audit. The next useful step is still clean production plus clean numeric role/usage, or a paid route/usage trial that passes the Post-Pro Phase 6 criteria.
