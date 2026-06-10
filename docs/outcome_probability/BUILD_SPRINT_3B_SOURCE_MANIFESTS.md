# Build Sprint 3B - Source Manifests And Data Readiness

Status: scaffold complete; Sprint 4 base rates are NOT READY.

Sprint 3B adds source-manifest, cutoff timestamp, source timestamp, raw-stat mapping, row-level leakage, and data-readiness tooling for the Outcome Probability HQ historical row factory.

This sprint does not train models, build base rates, create player probabilities, create app percentages, create rankings, push, or deploy.

## Files

- Service: `src/services/nwr_outcome_source_manifest_service.py`
- Tests: `tests/test_nwr_outcome_source_manifest_service.py`
- Documentation: `docs/outcome_probability/BUILD_SPRINT_3B_SOURCE_MANIFESTS.md`

## Source Manifest Design

The service models a row-family source manifest with:

- `SourceManifestEntry`
- `RowFamilySourceManifest`
- deterministic `manifest_id`
- deterministic `manifest_hash`
- source classification
- source max timestamp
- missing timestamp flag
- manual review flag
- readiness status

Supported source classifications:

- `allowed`
- `blocked`
- `unknown`
- `display_only`

Supported readiness statuses:

- `ready`
- `needs_data`
- `manual_review_required`
- `blocked`

Unknown source manifests are never allowed automatically. They become `manual_review_required`.

Forbidden path/header contexts are blocked, including:

- ADP
- FantasyPros
- public rankings
- consensus
- startup rankings
- trade calculators
- public projections
- RotoWire projections/rankings/outlooks/values
- market rank
- league rank
- prior fantasy draft history
- prior NWR private score
- same-season final stats as pre-season features
- hindsight notes
- post-cutoff updates

Display/context sources such as draft prep, prior league draft, market context, league context, and comparison-only files remain display-only/manual-review and are not training features.

## Row Family Manifests

Sprint 3B supports only the same v1 row families as Sprint 2 and Sprint 3:

- `rookie_post_draft`
- `all_player_pre_week1`
- `offseason_carryover`

Default required source families:

`rookie_post_draft`:

- `nwr_player_dim`
- `official_draft_capital`
- `nwr_historical_week_scores`
- `nwr_historical_season_labels`

`all_player_pre_week1`:

- `nwr_player_dim`
- `nwr_historical_week_scores`
- `nwr_historical_season_labels`

`offseason_carryover`:

- `nwr_player_dim`
- `nwr_historical_week_scores`
- `nwr_historical_season_labels`

Missing required source families block readiness.

## Cutoff Timestamp Design

Default cutoff definitions are contract placeholders:

- `rookie_post_draft_v1`: `YYYY-05-01`
- `all_player_pre_week1_v1`: `YYYY-09-01`
- `offseason_carryover_v1`: `YYYY-02-15`

The service expects real row-family runs to resolve these templates to concrete historical seasons before row emission.

Missing source timestamps block production row emission.

Accepted timestamp field names:

- `source_max_timestamp`
- `source_available_at`
- `collected_at_utc`
- `generated_at`
- `snapshot_date`
- `as_of_date`
- `source_date`

`calculate_source_max_timestamp()` returns the latest timestamp across source records. If no timestamp is available, it returns `None`, and the source entry becomes blocked when it is otherwise allowed.

## Label Availability Design

`label_available_date()` defines when labels are available:

- same-year / year-1 target: January 15 after target season
- next-year / year-2 target: January 15 two years after target season
- next-3-year target: January 15 three years after target season
- next-5-year target: January 15 five years after target season

Postseason/full-season-plus-playoffs windows use February 15 instead of January 15.

Future/censored windows return `needs_data` until the label availability date has passed.

Missing or unsupported label horizon returns `None` and must block materialization.

## Raw Stat Mapping Design

Sprint 3B maps historical raw stat fields into the Sprint 1 scoring components without calculating base rates.

Covered scoring components:

- `pass_yds`
- `pass_td`
- `pass_int`
- `pass_first_downs`
- `pass_2pt`
- `sacks_suffered`
- `carries`
- `rush_yds`
- `rush_td`
- `rush_first_downs`
- `rush_2pt`
- `receptions`
- `rec_yds`
- `rec_td`
- `rec_first_downs`
- `rec_2pt`
- `fumbles_lost`
- `return_yds`
- `return_td`
- `special_td`
- `fumble_recovery_td`
- `misc_yds`

`validate_raw_stat_mapping()` reports every component as:

- `ready` when an accepted alias is present
- `needs_data` when no accepted alias exists

This is mapping readiness only. It does not score weeks and does not build base-rate tables.

## Row-Level Leakage Audit Design

`audit_source_records_for_leakage()` reviews actual or fixture records and emits one row-level audit object per record.

It blocks:

- forbidden source/path/header/value context
- missing source timestamp
- post-cutoff source timestamp

It marks unknown sources as manual review instead of allowing them.

It returns `ready`, `manual_review_required`, or `blocked`; it does not produce probabilities or model outputs.

## Export Design

`write_source_manifest_exports()` writes only to an explicit caller-provided output folder:

- `row_family_source_manifests.csv`
- `source_manifest_entries.csv`
- `row_level_leakage_audit.csv`
- `raw_stat_mapping_readiness.csv`
- `data_readiness_report.csv`

These are dry-run/readiness exports, not production data packs.

## Real Data Sources Found

Local source candidates exist, but Sprint 3B does not yet select a real manifest:

- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_player_stats_weekly.csv`
- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_injuries_weekly.csv`
- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_participation_player_weekly.csv`
- `templates/real_data_inputs/historical_rookie_replay/pre_draft_prospect_inputs.csv`
- `templates/real_data_inputs/historical_rookie_replay/post_draft_outcomes.csv`
- `sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv`
- `sample_data/historical_rookie_replay/post_draft_outcomes.csv`
- existing Model v4 evidence matrices and historical rookie audit packets

These must be inspected in a real Sprint 3B dry-run manifest before Sprint 4. Some files are templates or samples, not authoritative historical feature rows.

## Data Readiness Report

`build_data_readiness_report()` combines:

- row-family manifest readiness
- row-level leakage audit readiness
- raw stat mapping readiness

Sprint 4 should start only when the readiness report is `ready`.

Current recommendation: NOT READY for Sprint 4 v0 base rates.

## Remaining Blockers Before Sprint 4

- Choose exact real files for each row family.
- Resolve concrete cutoff dates per historical season.
- Confirm source max timestamps on every source row.
- Confirm label availability dates per target horizon.
- Confirm raw stat fields cover all Sprint 1 scoring components needed for weekly scoring.
- Run row-level leakage audits against actual selected files.
- Produce dry-run exports under a local Sprint 3B output folder.
- Review unknown/display-only classifications.
- Decide how to handle missing first-down, injury, and opportunity fields.

## Next Step

Run a Sprint 3B dry-run source manifest pass against selected local historical files. Produce the five readiness export CSVs and only proceed to Sprint 4 if the data readiness report is `ready`.
