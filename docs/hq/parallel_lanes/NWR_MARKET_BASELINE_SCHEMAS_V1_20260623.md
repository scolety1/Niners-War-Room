# NWR Market Baseline Derived Schemas V1 - 2026-06-23

## Naming

Stable future artifact names:

- `dp_player_market_context.csv`
- `dp_pick_market_context.csv`
- `dp_playerid_crosswalk_audit.csv`
- `dp_nwr_join_coverage.csv`
- `dp_freshness_report.csv`

Current compatible names:

- `dp_market_baseline_context.csv` is accepted as the player context source.
- `dp_pick_value_context.csv` is accepted as the pick context source.

## Shared Freshness Columns

Required on all app-facing market artifacts except where noted:

- `nwr_fetch_timestamp`: ISO timestamp string, required when a cache exists.
- `upstream_scrape_date`: `YYYY-MM-DD` string, empty only for no valid cache.
- `upstream_latest_commit_sha`: string, empty only when unavailable.
- `upstream_latest_commit_timestamp`: ISO timestamp string, empty only when unavailable.
- `upstream_workflow_name`: string.
- `upstream_expected_cron`: string.
- `local_cache_path`: string, may point to ignored `C:\NWR_SHARED_DATA`.
- `derived_artifact_path`: string.
- `freshness_status`: one of the contract statuses.
- `market_baseline_stale_warning`: string, required for yellow/red statuses.

Allowed missing values: empty string for unavailable timestamps, commit fields, cache paths,
or warnings when status is green.

## dp_player_market_context.csv

Required columns:

- `player`: string.
- `pos`: string position.
- `team`: string, empty allowed.
- `age`: numeric string, empty allowed.
- `draft_year`: integer string, empty allowed.
- `ecr_1qb`: numeric string, empty allowed only if upstream missing.
- `ecr_pos`: numeric string, empty allowed.
- `value_1qb`: numeric string, empty allowed only if upstream missing.
- `scrape_date`: `YYYY-MM-DD`.
- `fp_id`: string, empty allowed.
- `sleeper_id`: string, empty allowed.
- `nwr_player_id`: string, empty allowed.
- `nwr_name`: string, empty when unmatched.
- `nwr_pos`: string, empty when unmatched.
- `nwr_final_board_rank`: numeric string, empty allowed.
- `nwr_dynasty_rank`: numeric string, empty allowed.
- `nwr_candidate_rank`: numeric string, empty allowed.
- `dp_market_rank_1qb`: numeric string.
- `dp_value_1qb`: numeric string.
- `nwr_vs_dp_gap`: numeric string, empty when no NWR rank basis.
- `market_sanity_flag`: legacy builder label, display-only.
- `join_method`: `sleeper_id`, `gsis_id`, `fp_id`, `exact_name_position`,
  `normalized_name_position`, or `unmatched`.
- `join_confidence`: `high`, `medium`, `review`, or `none`.
- `source_note`: string attribution.
- `dp_display_only_warning`: required display-only warning.
- Shared freshness columns.

Optional columns:

- `market_baseline_label`.
- `market_sanity_label`.
- `market_gap`.
- `market_baseline_stale_warning`.

Freshness requirement: yellow/red rows must show stale language in the page surface.

Join confidence rule: exact ID is high, exact name plus position is medium, normalized name
plus position is review, unmatched is manual review.

Display-only warning fields: `dp_display_only_warning`, `market_baseline_label`, and
`market_baseline_stale_warning`.

## dp_pick_market_context.csv

Required columns:

- `pick_label`: string such as `2026 1.04`, `2026 2.03`, or `2028 1st`.
- `value_1qb`: numeric string.
- `ecr_1qb`: numeric string.
- `scrape_date`: `YYYY-MM-DD`.
- `source_note`: string attribution.
- Shared freshness columns.

Optional columns:

- `ecr_2qb`.
- `pick`.
- `market_baseline_label`.

Allowed missing values: no missing `pick_label`; numeric fields may be empty only when
upstream is missing and the row is displayed as unavailable.

Freshness requirement: same as player context.

Join confidence rule: pick lookup is exact normalized label only. Do not infer missing picks.

Display-only warning fields: `source_note`, `market_baseline_label`,
`market_baseline_stale_warning`.

## dp_playerid_crosswalk_audit.csv

Required columns:

- `player`
- `pos`
- `team`
- `fp_id`
- `sleeper_id`
- `nwr_player_id`
- `nwr_name`
- `nwr_pos`
- `join_method`
- `join_confidence`
- `source_note`
- `dp_display_only_warning`
- Shared freshness columns.

Optional columns:

- `gsis_id`
- `birthdate`
- `manual_review_note`

Allowed missing values: external IDs may be empty; matched `nwr_name` and `nwr_pos` must be
present for included crosswalk rows.

Freshness requirement: same as player context.

Join confidence rule: same as player context.

Display-only warning fields: `dp_display_only_warning`, `market_baseline_stale_warning`.

## dp_nwr_join_coverage.csv

Required columns:

- `source_name`: string.
- `nwr_rows`: integer string.
- `dp_matched_rows`: integer string.
- `dp_match_rate`: decimal string.
- `nwr_age_rows_before_dp`: integer string.
- `dp_age_rows_when_matched`: integer string.
- `age_gain_possible_rows`: integer string or review text.
- `notes`: string with display-only warning.
- Shared freshness columns.

Optional columns:

- `manual_review_rows`.
- `unmatched_rows`.

Allowed missing values: only optional review fields may be empty.

Freshness requirement: same as player context.

Join confidence rule: coverage aggregates must be derived from the player-context join path.

Display-only warning fields: `notes`, `market_baseline_stale_warning`.

## dp_freshness_report.csv

Required columns:

- `nwr_fetch_timestamp`
- `upstream_scrape_date`
- `upstream_latest_commit_sha`
- `upstream_latest_commit_timestamp`
- `upstream_workflow_name`
- `upstream_expected_cron`
- `local_cache_path`
- `derived_artifact_path`
- `freshness_status`
- `freshness_age_days`
- `previous_scrape_date`
- `previous_values_sha256`
- `current_values_sha256`
- `freshness_warning`
- `market_baseline_stale_warning`

Optional columns:

- `upstream_expected_utc`
- `nwr_recommended_pull`
- `nwr_backup_retry`

Allowed missing values: commit, cache, and scrape fields may be empty only for
`RED_NO_VALID_CACHE`.

Freshness requirement: `freshness_status` must be one of the contract statuses.

Join confidence rule: not applicable.

Display-only warning fields: `freshness_warning`, `market_baseline_stale_warning`.
