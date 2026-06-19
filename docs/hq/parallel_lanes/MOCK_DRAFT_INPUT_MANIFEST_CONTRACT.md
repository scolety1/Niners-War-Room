# Mock Draft Input Manifest Contract

## Purpose

Future real input paths should be configured through a local-only manifest,
not committed into the repo.

Recommended path:

`local_exports/mock_draft/manual_input_manifest.local.json`

## Rules

- The manifest is local-only and must not be committed.
- Missing manifest is YELLOW, not RED.
- Malformed manifest is RED when validating it.
- The manifest may include file paths and input roles only.
- The manifest must not include actual rankings, probabilities, bands,
  promoted artifacts, or generated outputs.
- NWR private value source must stay separate from ADP/market behavior context.
- ADP/market context may support opponent behavior, availability, and likely
  pick timing only.

## Required Roles

- `frozen_rookie_input`
- `veteran_pool`
- `pick_order`
- `my_picks`
- `rosters`
- `team_needs`
- `nwr_private_values`
- `market_context`

## Example Shape

```json
{
  "version": 1,
  "review_only": true,
  "inputs": {
    "frozen_rookie_input": {
      "role": "frozen_rookie_input",
      "path": "local_exports/.../rookie_2026_mock_draft_input_20260616.csv"
    }
  }
}
```
