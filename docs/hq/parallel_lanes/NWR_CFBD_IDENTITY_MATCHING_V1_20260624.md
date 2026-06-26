# NWR CFBD Identity Matching V1 - 2026-06-24

## Verdict

GREEN for review-only identity matching artifacts.

This lane uses already-integrated CFBD review artifacts and existing tracked player identity/reference artifacts. It does not repull CFBD, use secrets, or promote CFBD data into any model/rank/source-truth output.

## Starting HEAD

`3c06623d7dc511d2dc4db0d2131776b42d8def36`

## Worktree / Branch

- Worktree: `C:\NWR\Niners-War-Room-cfbd-identity-matching-v1`
- Branch: `codex/cfbd-identity-matching-v1-20260624`
- Base: `origin/work/hq-parallel-control`

## Input CFBD Rows

- Input artifact: `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_identity_review_queue.csv`
- Input rows: 31,822
- Input status: review-only, model use disallowed, training disallowed, identity review required.

## Identity Sources Used

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_review.csv`
- `docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv`
- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
- `docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv`
- `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_playerid_crosswalk_audit.csv`
- `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- `sample_data/2026_pre_declaration/dim_players.csv`

These were used as review/reference candidates only. They were not modified.

## Matching Method

- Normalize names by ASCII folding, suffix cleanup, punctuation/apostrophe/hyphen removal, and lowercasing.
- Preserve existing explicit aliases for `KC Concepcion` and `Nick Singleton`.
- Prefer exact normalized-name matches with compatible position.
- Use deterministic fuzzy fallback with Python `SequenceMatcher` for same-position, same-first-letter candidates.
- Require fuzzy score at least 88 for a review candidate.
- Mark multiple plausible logical identities as `ambiguous`.
- Keep all matches human-review required, including `HIGH` confidence rows.

## Match Counts

Source-row status counts:

| Match status | Count |
|---|---:|
| exact_match | 157 |
| strong_candidate | 0 |
| possible_candidate | 46 |
| ambiguous | 5 |
| unmatched_review_required | 31,614 |

Source-row confidence counts:

| Confidence | Count |
|---|---:|
| HIGH | 157 |
| MEDIUM | 5 |
| LOW | 46 |
| UNKNOWN | 31,614 |

Candidate output rows after final dedupe: 31,827. Candidate-source spam was reduced by selecting one representative source per logical candidate identity.

## Ambiguous / Unmatched Counts

- Ambiguous source rows: 5
- Unmatched source rows: 31,614
- Ambiguous/non-high review CSV rows: 31,670
- Unmatched review CSV rows: 31,614

## Artifacts Created

Tracked under `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/`:

- `README.md`
- `cfbd_identity_matching_method.md`
- `cfbd_identity_match_candidates.csv`
- `cfbd_identity_match_summary.csv`
- `cfbd_identity_ambiguous_review.csv`
- `cfbd_identity_unmatched_review.csv`
- `cfbd_identity_high_confidence_review.csv`
- `cfbd_identity_possible_review.csv`
- `cfbd_identity_unmatched_priority_review.csv`
- `cfbd_identity_link_registry_DRAFT.csv`
- `cfbd_identity_review_dashboard_summary.csv`
- `cfbd_identity_production_context_review.csv`
- `cfbd_identity_final_review_method.md`

## Review-Only Confirmation

All output rows use:

- `review_required=true`
- `model_use_allowed=false`
- `training_allowed=false`

The outputs are not source truth, not model input, not training truth, and not candidate/rank outputs.

## NFL Usage/Data-Loader Isolation

Confirmed untouched by this lane:

- `docs/hq/data_sources/nfl_usage/historical_panel/`
- `scripts/build_historical_nfl_usage_panel_v0.py`
- `src/services/nfl_usage_historical_panel_service.py`
- `tests/test_nfl_usage_historical_panel_service.py`

No nflverse/NFL usage/data-loader logic was changed.

## Tests / Checks

- Focused pytest: `tests/test_cfbd_identity_matching_v1.py`
- Ruff on touched Python files.
- Python compile on touched Python files.
- CSV load/schema/flag validation.
- `git diff --check`.
- Git status review.

## Guardrails

Confirmed:

- Frozen Final Draft Board V1 row count remains 66.
- Pinned snapshot unchanged.
- `latest_candidate` / `latest_approved` untouched.
- No `final_board_rank`, Dynasty Rank, Candidate Rank, tier, model/rank/source-truth mutation.
- No Gmail/vendor/RotoWire scraping.
- No CFBD API key used or printed.
- No `C:\NWR_LOCAL_SECRETS` files tracked.
- No `C:\NWR_SHARED_DATA` files tracked.

## Remaining Recommended Next Step

Run a human review pass on:

1. `cfbd_identity_ambiguous_review.csv`
2. `cfbd_identity_unmatched_review.csv`
3. The `HIGH` confidence rows in `cfbd_identity_match_candidates.csv`

Only after manual approval should a future lane design a promotion gate or any source-truth crosswalk.

## Finalization Addendum

Final review-ready artifacts were added to separate the queue into human-review slices:

- High-confidence review rows: 157
- Possible/ambiguous review rows: 56
- Unmatched priority rows: 31,614
- Draft registry rows: 213
- Candidate rows with production context: 5,817
- Distinct CFBD player-season rows with production context in the dashboard: 5,809
- Recruiting context rows: 0, because V1 has no tracked row-level recruiting artifact

The draft registry remains `DRAFT_REVIEW_ONLY`; every row has `approved_by_human=false`, `model_use_allowed=false`, and `training_allowed=false`.

Final review files added:

- `cfbd_identity_high_confidence_review.csv`
- `cfbd_identity_possible_review.csv`
- `cfbd_identity_unmatched_priority_review.csv`
- `cfbd_identity_link_registry_DRAFT.csv`
- `cfbd_identity_review_dashboard_summary.csv`
- `cfbd_identity_production_context_review.csv`
- `cfbd_identity_final_review_method.md`

Finalization confirms no model use, no source-truth promotion, and readiness for Master integration review.
