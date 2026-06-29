# Injury Context Source Gate

## Decision

APPROVE_INJURY_CONTEXT_REVIEW_ONLY.

This is a narrow source gate for factual injury/availability context only. It is
not approval for medical predictions, source truth, model training, hidden sort,
rank adjustments, trade value, pick value, or app-facing probabilities.

## Source Inspected

Loader:

- `nflreadpy.load_injuries`
- Observed package version: `0.1.5`
- Data dictionary reference inside package docstring:
  `https://nflreadr.nflverse.com/articles/dictionary_injuries.html`

Generated local raw review-only output, not committed:

- `C:\NWR_SHARED_DATA\injury_context\nflreadpy_injuries_review_only_2012_2025.csv`

Generated audit artifacts, not committed:

- `C:\NWR_SHARED_DATA\injury_context\injury_context_source_gate_audit.csv`
- `C:\NWR_SHARED_DATA\injury_context\injury_context_source_gate_manifest.csv`

## Coverage

| Item | Result |
| --- | --- |
| Decision | APPROVE_INJURY_CONTEXT_REVIEW_ONLY |
| Rows | 76469 |
| Seasons | 2012-2025 |
| Teams | 35 |
| Players | 5855 |
| GSIS coverage | 1.000000 |
| Loader status | nflreadpy 0.1.5 load_injuries available |

Fields present:

- `season`
- `game_type`
- `team`
- `week`
- `gsis_id`
- `position`
- `full_name`
- `report_primary_injury`
- `report_secondary_injury`
- `report_status`
- `practice_primary_injury`
- `practice_secondary_injury`
- `practice_status`
- `date_modified`

## Source-Policy Status

The NWR source inventory classifies nflverse as public structured NFL facts and
lists injuries as available factual context. This gate approves only
review-only context from the `nflreadpy.load_injuries` factual loader.

Approved use:

- `injury_context_review_only`

Not approved:

- model training
- source truth
- Rankings rank logic
- hidden sort
- trade value
- pick value
- medical prediction
- player-specific recovery probability
- app-facing Outcome V2 probabilities

## Joinability

The injury rows include `gsis_id`, which is compatible with Outcome V2 historical
labels and the current-board-to-GSIS identity bridge. This gate does not perform
app integration or current-player probability generation.

## Safe Context Flags For Later Review

The source can support future review-only or display-only availability context
flags if a later lane explicitly approves them:

- `injury_context_available`
- `missed_prior_season`
- `limited_recent_sample`
- `last_materially_active_season`
- `seasons_since_material_activity`
- `availability_caveat`
- `not_enough_information_reason`

## Explicitly Blocked Outputs

The following remain blocked:

- injury risk score
- medical recovery probability
- ACL comeback projection
- Achilles comeback projection
- player-specific recovery prediction
- hidden rank adjustment
- trade or pick valuation

## Remaining Caveats

- Injury reports are factual status rows, not medical recovery forecasts.
- A missing injury row is not evidence of clean health.
- Historical report availability can vary by season and week.
- This gate does not decide whether injury context belongs in Outcome Lens.
- This gate does not alter RB elite/intermediate threshold status.

## Guardrails

- Raw injury data remains under `C:\NWR_SHARED_DATA` and is not tracked.
- No app code was touched.
- No Rankings, Outcome Lens, Dynasty Rank, tiers, hidden sort, trade value, pick
  value, Live Draft, Mock Draft, or runtime behavior was changed.
- No vendor, Gmail, CFBD, market, ADP, DynastyProcess, projection, or analyst
  rank source was used.
- No medical-style field names or recovery projections were introduced.
