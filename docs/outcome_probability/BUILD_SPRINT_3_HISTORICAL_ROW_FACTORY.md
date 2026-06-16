# Build Sprint 3 - Historical Row Factory And Source Inventory

Status: read-only scaffold. No player probabilities, app percentages, base rates, model training, rankings, or deployment changes.

## Purpose

Sprint 3 connects the Sprint 1 scoring/label scaffold to the Sprint 2 point-in-time row contracts. The goal is to prove whether legal historical rows can be emitted from source-safe local data.

This sprint does not optimize model performance. It creates:

- a historical source inventory contract
- a read-only row factory
- source coverage and missingness summaries
- dry-run export contracts

## Supported Row Families

Only these v1 row families are supported:

- `rookie_post_draft`
- `all_player_pre_week1`
- `offseason_carryover`

Unsupported families, including pre-draft rookie and in-season rows, are rejected.

## Service

Implementation:

- `src/services/nwr_outcome_historical_row_factory.py`

Tests:

- `tests/test_nwr_outcome_historical_row_factory.py`

The service uses Sprint 2 objects directly:

- `PredictionSnapshot`
- `FeatureSnapshot`
- `TrainingRow`
- `SourceAllowlistRule`
- `FeatureLegalityAudit`
- deterministic `row_id`
- deterministic `snapshot_hash`
- missingness masks
- label availability materialization gate

## Historical Source Inventory

`build_historical_source_inventory()` inspects local CSV-like source paths and classifies each source as:

- `allowed`
- `blocked`
- `unknown`
- `display_only`

Forbidden source families are blocked when a path/header references prohibited inputs such as ADP, FantasyPros, public projections, consensus, startup rankings, trade calculators, market rank, league rank, prior draft history, RotoWire rankings/projections/outlooks/values, legacy private score, prior model outputs, or hindsight notes.

Unknown sources are never allowed automatically. They are marked as manual-review required.

Display/context sources such as prior draft prep or market context are not training features.

The inventory reports:

- source path
- source family
- classification
- row count
- columns
- required identity fields present/missing
- manual review requirement
- notes

## Candidate Row Emission

`emit_candidate_training_row()` takes a player record, a `PredictionSnapshot`, source-safe `FeatureSnapshot` records, and an `as_of_date`.

It blocks row emission when:

- row family is unsupported
- required identity fields are missing
- stale prior-row reuse is detected
- feature legality fails
- the label is not yet available

Feature legality is delegated to the Sprint 2 validator. The row factory does not bypass that validator.

Missing optional features are carried as `None` in the feature vector and marked in the missingness mask. They are not zero-filled.

Training rows are only materialized when `as_of_date >= label_available_date`.

## Stale Prior-Row Reuse

Sprint 3 explicitly rejects:

- rows flagged with `stale_prior_row`
- rows carrying a `prior_row_cutoff_id` that does not match the current prediction snapshot cutoff

Future real source ingestion should extend this into a row-level stale-source audit.

## Source Coverage Reports

`coverage_reports()` emits summary rows for:

- player identity coverage
- feature legality coverage
- materialized training row count
- first-down field coverage
- injury/opportunity coverage

`missingness_summary()` aggregates missing optional features.

`blocked_source_summary()` aggregates source inventory classifications.

## Dry-Run Export Contracts

`write_dry_run_exports()` writes only to a caller-provided output folder. It does not mutate production data.

Dry-run export files:

- `historical_source_inventory.csv`
- `candidate_training_rows_dry_run.csv`
- `source_coverage_report.csv`
- `missingness_summary.csv`
- `blocked_forbidden_source_summary.csv`

These are contracts for Sprint 4-readiness inspection, not model outputs.

## Real Local Data Sources Found

Existing repo/local data that can later feed a real row factory, after source and timestamp review:

- Sprint 1 scoring config and scoring service
- local historical rookie replay samples
- post-draft outcome samples
- model v4 evidence matrices
- local RotoWire factual/raw stats, role usage, workouts, injury/status context
- official/local draft capital snapshots
- NWR player identity and ranking exports for display/context checks only

Blocked/display-only sources already identified by policy:

- market rank / league rank
- public or consensus rank/projection fields
- RotoWire ranking/projection/outlook/value fields
- prior fantasy draft history
- legacy active-pack/private score fields

## Blockers Before v0 Base Rates

Before Sprint 4 can build v0 base rates, NWR needs:

1. A real source manifest for each row family.
2. Point-in-time cutoff dates and source max timestamps for each feature source.
3. Historical raw stat rows mapped into Sprint 1 scoring components.
4. Historical label availability dates.
5. Row-level leakage audit exports from actual files.
6. Identity coverage reports across historical seasons.
7. Confirmation that first-down and injury/opportunity fields are available or intentionally missing.

## Sprint 4 Next Step

Sprint 4 should build a v0 historical base-rate engine from audited legal rows only. It should not use any row that fails the Sprint 2 legality checks or Sprint 3 source inventory gates.
