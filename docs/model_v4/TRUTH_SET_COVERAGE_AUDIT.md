# Model v4 Truth Set Coverage Audit

Created: 2026-05-16

This audit checks whether the broad Model v4 truth set has enough currently
available evidence to support formula rebuild work. It does not score players,
change formulas, unlock readiness, or promote rankings.

Machine-readable file:

- `docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.csv`

## Source Inputs Checked

- `truth_set`: `docs\model_v4\TRUTH_SET_PLAYER_UNIVERSE.csv`
- `v3_2_promotion_root`: `local_exports\truth_set_lab\v3_2\promoted_review_models\truth_set_v3_2_promoted_review_20260515T212700Z`
- `active_public_source_root`: `local_exports\active_veteran_model_public_sources`
- `young_bridge_path`: `local_exports\truth_set_lab\v2\reports\young_bridge_prior_preview.csv`
- `roster_rank_path`: `docs\model_v4\official_inputs\NINERS_ROSTER_RANKS_20260331.csv`

## Summary

| Metric | Value |
| --- | --- |
| truth_set_players | 80 |
| ready | 0 |
| review | 80 |
| blocked_missing_input | 0 |
| players_with_formula_rebuild_blockers | 0 |
| players_with_review_warnings | 80 |

## Formula Rebuild Blockers

No formula rebuild blockers were found.

## Review Warning Counts

| Warning | Players |
| --- | --- |
| first_downs_review | 40 |
| identity_review | 1 |
| injury_context_gap | 37 |
| market_context_gap | 80 |
| missing_age_bio | 5 |
| missing_young_prior | 5 |
| production_review | 40 |
| projection_gap | 44 |
| snap_share_gap | 40 |
| usage_review | 40 |
| young_prior_preview_only | 6 |

## Interpretation

- `blocked_missing_input` means a player lacks evidence needed before formula
  rebuild fixtures can fairly evaluate that player.
- `review` means formula work can proceed, but receipts must surface the gap.
- Projection, injury, and market gaps are review warnings unless a later
  contract explicitly promotes them to blocking status.
- Incoming rookies are expected to lack NFL production, usage, and snap data;
  their key blocker is missing identity or young/prospect prior evidence.
