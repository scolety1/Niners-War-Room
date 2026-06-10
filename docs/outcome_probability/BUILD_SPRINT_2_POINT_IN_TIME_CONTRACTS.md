# Build Sprint 2 - Point-in-Time Training Row Contracts

Status: scaffolded, no player probabilities created.

This sprint creates the row contracts and validators needed before any NWR outcome probability model can be trained. It does not train models, create base rates, create app percentages, create rankings, or write player probability outputs.

## Supported Row Families

Sprint 2 supports these v1 row families only:

- `rookie_post_draft`
- `all_player_pre_week1`
- `offseason_carryover`

Pre-draft rookie rows and in-season rows are intentionally out of scope.

## Contract Concepts

The repo does not currently require SQL persistence for these rows, so Sprint 2 implements Python dataclass/dataframe-style contracts in [src/services/nwr_outcome_training_row_service.py](../../src/services/nwr_outcome_training_row_service.py).

The scaffold covers:

- `nwr_prediction_snapshots`
- `nwr_feature_snapshots`
- `nwr_training_rows`
- `nwr_source_allowlist`
- `nwr_feature_legality_audit`
- `nwr_model_split_registry`

Every training row includes the required Sprint 2 fields:

- `row_id`
- `player_id`
- `player_name`
- `position`
- `row_type`
- `cutoff_id`
- `prediction_date`
- `input_snapshot_date`
- `source_max_timestamp`
- `label_available_date`
- `target_season`
- `target_horizon`
- `team_at_snapshot`
- `age_at_snapshot`
- `experience_at_snapshot`
- `feature_vector`
- `missingness_mask`
- `outcome_window`
- `label_schema_version`
- `source_manifest`
- `parser_version`
- `snapshot_hash`
- `manual_review_status`

`probability_status` is included as a status/display field only. It is not a probability.

## Row ID Logic

`row_id` is deterministic and generated from stable business keys:

- row type
- player id
- position
- cutoff id
- input snapshot date
- target season
- target horizon

The generated value is a stable SHA-256-derived id prefixed with `nwr_tr_`.

## Snapshot Hash Logic

`snapshot_hash` is a deterministic SHA-256 hash of the canonicalized training row payload before `snapshot_hash` itself is attached. The canonicalizer sorts mapping keys and normalizes dates/datetimes to ISO strings so equivalent payloads hash consistently.

Changing the feature payload changes `snapshot_hash`.

## Source Allowlist

Allowed source families are scaffolded only when timestamp and lineage checks pass:

- `nwr_scoring_rules`
- `nwr_player_dim`
- `nwr_historical_week_scores`
- `nwr_historical_season_labels`
- `nflverse_raw_stats`
- `rotowire_raw_stats`
- `rotowire_role_usage`
- `rotowire_workouts`
- `official_draft_capital`
- `injury_status_source`
- `manual_private_scouting_notes`

Blocked source families include:

- ADP
- FantasyPros
- public rankings, consensus, projections
- startup rankings
- trade calculators
- market rank
- league rank
- RotoWire projections, rankings, outlooks, values
- prior fantasy draft history
- legacy/private-score snapshots
- prior NWR model outputs
- hindsight notes

RotoWire raw status/usage-style sources may be allowed only as source-safe factual inputs with point-in-time receipts. RotoWire rankings/projections/outlooks/values remain blocked.

## Feature Legality Audit

The feature legality validator checks:

- source family is allowlisted
- blocked source families fail
- feature/source-field names do not reference forbidden input families
- source availability timestamp is on or before `input_snapshot_date`
- source max timestamp is on or before `input_snapshot_date`
- future-data flags fail
- target-window overlap fails
- lineage receipts are present

Player identity fields (`player_id`, `player_name`) are retained on the row for joins and display, but are blocked from `feature_vector`.

## Missingness Mask

Missingness is explicit. `None` and blank strings are marked as missing in `missingness_mask` and are not zero-filled. Future modeling can choose how to handle missing values, but Sprint 2 preserves the original null state.

## Label Availability Gate

Training rows are not materialized before `label_available_date`. This prevents censored rows from slipping into a training set before outcomes are observable.

## Walk-Forward Split Registry

`model_split_registry_skeleton()` defines walk-forward split metadata only. It does not train a model and does not select final splits.

## App Probability Statuses

Allowed app/status-safe values:

- `ready`
- `in_development`
- `needs_data`
- `model_unavailable`
- `insufficient_evidence`
- `not_applicable`
- `leakage_audit_failed`
- `source_stale`
- `manual_review_pending`

These are statuses only; no player probabilities are produced in Sprint 2.

## Prior-Prep File Separation

The earlier outcome-column integration prep files are separate from Sprint 2. They are not required by the training row contract service and should not be included in a Sprint 2-only commit unless explicitly approved later.

## Sprint 3 Next Step

Sprint 3 can begin only after these contracts are accepted. The next step should be a read-only historical row factory that emits point-in-time rows from known historical sources and produces leakage reports. It should still avoid player probabilities until the rows and labels are audited.
