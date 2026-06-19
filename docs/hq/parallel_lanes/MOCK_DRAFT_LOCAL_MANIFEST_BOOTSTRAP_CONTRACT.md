# Mock Draft Local Manifest Bootstrap Contract

## Purpose

The real input manifest is a future local-only operator file. This runway
defines how to prepare its shape without creating, writing, staging, or
committing real input paths.

Expected local-only path:

`local_exports/mock_draft/manual_input_manifest.local.json`

## Required Roles

- `rookie_input`
- `veteran_pool`
- `pick_order`
- `my_picks`
- `rosters_keepers`
- `team_needs`
- `nwr_private_values`
- `market_context`

## Allowed Contents

- local CSV paths;
- input roles;
- source notes;
- manual review notes;
- source freshness notes;
- ADP/market separation notes.

## Forbidden Contents

- real output exports;
- probabilities or probability bands;
- promoted artifacts;
- production rankings or sorting keys;
- generated simulator outputs;
- real player rows pasted into committed docs.

## Source Separation

ADP/market context is allowed only for opponent behavior, likely availability,
and pick timing. It must never become NWR private quality or value. NWR private
value and market context must remain separate roles and files.

## No-Simulation Gate

Missing manifest is YELLOW, not RED. A manifest that exists but has malformed
roles or unsafe source mixing is RED. No mock draft simulation may run until all
real inputs are present, validated, and manually reviewed.
