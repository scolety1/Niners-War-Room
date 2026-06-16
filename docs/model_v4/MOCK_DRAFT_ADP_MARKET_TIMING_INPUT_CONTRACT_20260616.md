# Mock Draft ADP/Market Timing Input Contract - 2026-06-16

## Scope
- Lane: `work/mock-draft-simulator`.
- Purpose: define the review-only input contract for optional ADP/market timing rows used to calibrate opponent behavior in the Mock Draft HQ lane.
- This contract does not promote or import real ADP data. It only defines the safe shape and guardrails for future behavior-only timing inputs.
- The current lane has review-only mock draft services and local artifacts, but no dedicated committed mock-draft ADP/market timing input file.

## Approved Behavior-Only Columns
Approved columns may be used only to estimate opponent pick timing, player availability, and behavior-only notes:

| Column | Required | Approved use |
| --- | --- | --- |
| `asset_id` | yes | Join to the combined simulator state row. |
| `player` | recommended | Human review label and identity cross-check. |
| `position` | optional | Identity review and behavior notes only. |
| `source_name` | yes | Source lineage and auditability. |
| `source_type` | yes | Must describe market/ADP/timing context, not NWR value. |
| `source_timestamp` | yes | Staleness review. |
| `market_adp` | optional | Opponent timing window only. |
| `overall_adp` | optional | Opponent timing window only. |
| `expected_pick` | optional | Opponent timing window only. |
| `adp_min` | optional | Availability stress-test context only. |
| `adp_max` | optional | Availability stress-test context only. |
| `sample_size` | optional | Source quality note only. |
| `league_format_note` | optional | Review context only. |
| `identity_match_method` | recommended | Matching audit only. |
| `review_flags` | optional | Human review flags only. |

At least one of `market_adp`, `overall_adp`, or `expected_pick` must be present for a row to influence opponent timing. Rows without usable timing remain review-required or fall back to deterministic placeholder behavior.

## Disallowed Columns And Uses
The following columns are blocked from all market timing inputs and must be ignored if present:

- `stats_model_value`
- `model_value`
- `draft_value`
- `nwr_draft_value`
- `nwr_dynasty_score`
- `nwr_quality_score`
- `quality_score`
- `war_score`
- any production ranking, sorting, hidden sort key, or private value replacement field

Disallowed uses:

- entering NWR private quality/value
- altering frozen rookie `rank`, `tier`, `draft_action`, warnings, notes, formula metadata, or board order
- backfilling missing NWR scores
- ranking value-neutral veterans/free agents against frozen rookies as NWR quality
- changing app-facing outputs, production rankings, production sorting, or promoted artifacts

## Source Lineage Requirements
Every accepted market timing row must preserve:

- source name and source type
- source timestamp or export date
- import timestamp when copied into this lane
- file path or manual provenance note
- explicit review-only status
- explicit note that market timing is behavior-only and not NWR quality

Real market data must not be added unless it already exists inside this mock-draft lane or is explicitly imported as local-only review input in a later approved step.

## Review Flags
Market timing rows must surface, not hide, these conditions:

| Flag | Meaning |
| --- | --- |
| `market_timing_missing_row_review_required` | Player has no timing row and uses fallback behavior-only availability logic. |
| `market_timing_stale_review_required` | Source timestamp is stale or not acceptable for draft-day prep. |
| `market_timing_ambiguous_identity_review_required` | Market row cannot be confidently matched to one simulator asset. |
| `market_timing_duplicate_identity_review_required` | Multiple market rows map to the same asset. |
| `market_timing_missing_pick_value_review_required` | Row exists but has no usable `market_adp`, `overall_adp`, or `expected_pick`. |
| `market_score_fields_ignored` | Blocked score/value fields were present and ignored. |
| `market_behavior_context_used` | Market timing influenced opponent timing or availability only. |

## Identity Matching Rules
- Primary match is `asset_id` from the combined simulator state.
- Player-name-only matching is review-required unless paired with position and a unique asset in the combined state.
- Duplicate names, duplicate drop declarations, and unresolved declarations remain separate rows until manually resolved.
- Market rows must never collapse duplicate declared drops such as the unresolved Brock Purdy duplicate declaration.
- Missing identity fields do not get filled from ADP/market data; they become review-required.

## Opponent Behavior Rules
- Market timing can move an opponent selection into or out of a likely pick window.
- Market timing can annotate likely availability at Tim/Niners pick windows.
- Market timing can create behavior-only notes such as `opponent_behavior_market_timing`.
- Market timing cannot make an automatic Tim/Niners best-pick decision.
- Tim/Niners outputs remain manual-review only.
- If no usable market timing exists, the simulator uses deterministic fallback behavior and marks the result review-only.

## Contamination Proof Requirements
Any implementation that consumes this contract must prove:

- market timing fields do not overwrite rookie `rank`, `tier`, `draft_action`, warning, or draft-room note fields
- market timing rows cannot create numeric NWR scores
- blocked score/value columns are ignored and reported
- value-neutral flags remain on declared drops and free agents
- missing market rows use fallback behavior-only logic or review-required flags, not NWR value
- app wiring, production rankings, production sorting, Rookie HQ, Outcome HQ, and Drop Decision HQ remain untouched

## Current Lane Inventory
- Dedicated committed mock-draft ADP/market timing input files found: none.
- Existing mock-draft code already accepts optional in-memory `market_context_rows` for opponent behavior tests and run-report generation.
- Existing local-only run artifacts include behavior notes and `market_context_used` fields, but they are outputs, not approved market timing source inputs.

## Verdict
This contract is GREEN as a guardrail. It is not a GREEN signal to import or promote real market data; a later step must explicitly approve any real local-only timing source.
