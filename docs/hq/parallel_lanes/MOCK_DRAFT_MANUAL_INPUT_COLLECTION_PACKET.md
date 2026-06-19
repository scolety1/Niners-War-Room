# Mock Draft Manual Input Collection Packet

## Needed Before Simulation

1. Frozen rookie input at the approved local-only path.
2. Dropped/available veteran pool.
3. Final pick order.
4. NWR/my pick numbers.
5. Rosters/keepers.
6. Team needs/opponent tendencies.
7. NWR private value source.
8. ADP/market behavior context.

## CSV Expectations

Each CSV must match the schema in `MOCK_DRAFT_INPUT_SCHEMA_CONTRACT.md`.
Market context must include a behavior-only allowed-use note. NWR private value
files must not include ADP, market rank, market value, opponent likelihood,
probability, band, app route, hidden sort, or promoted artifact columns.

## Local-Only Rules

Keep real files under ignored local-only paths such as `local_exports/`. Never
commit real draft input files, `data/`, `.venv/`, logs, caches, egg-info, or
generated exports.

## Readiness Colors

- GREEN: schema valid and source separation preserved.
- YELLOW: real input missing or not configured.
- RED: malformed schema, contamination columns, duplicate identities, or unsafe
  source mixing.

## Next Codex Prompt

“Validate the Mock Draft real input manifest at
`local_exports/mock_draft/manual_input_manifest.local.json` read-only. Do not
run simulations. Report GREEN/YELLOW/RED readiness and source-separation
findings.”

No simulation may run until inputs validate.

## Diagnostics Addendum

Use the manual column mapping packet before accepting messy real CSV headers.
Run schema diagnostics and header alias checks read-only, then update the
local-only manifest only after user approval. Fixture and adversarial tests are
GREEN infrastructure; real-input readiness remains YELLOW until all local files
are present.
