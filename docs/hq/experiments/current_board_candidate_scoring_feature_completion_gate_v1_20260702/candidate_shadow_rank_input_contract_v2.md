# Candidate Shadow Rank Input Contract V2

Candidate: `wr_boundary_breakout_sensitivity_guard`

Input status: `SCORING_FEATURES_COMPLETED_FOR_READY_ROWS`

Allowed next use:

- Calculate review-only candidate shadow scores/ranks outside app/runtime paths for rows where `candidate_feature_ready == true`.
- Preserve null-fenced rows as `Not enough information`.
- Join any later static shadow comparison by stable player id only.

Blocked:

- App wiring.
- Live preview.
- Production rankings.
- Hidden sort.
- Recommendations.
- Source-truth promotion.
- Production formula/config changes.
- Candidate output wiring into NWR.

The outside completed feature input is not itself a rank output and is not production-approved.
