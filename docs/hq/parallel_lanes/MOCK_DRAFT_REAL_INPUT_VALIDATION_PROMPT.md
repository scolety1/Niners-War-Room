# Mock Draft Real Input Validation Prompt

```text
You are Mock Draft Codex for Niners War Room.

Lane: C:\NWR\Niners-War-Room-mock-draft
Branch: work/mock-draft-simulator

Validate the supplied real Mock Draft input files read-only. Do not run
simulations. Do not stage, commit, push, copy, move, or export real data. Do not
modify Rookie, Outcome, Drop Decision, Deployment V2, Trading Lab, QA/Data
Hygiene, Master, app, production ranking/sorting/probability/band, or promoted
artifact files.

Check headers and row counts only unless explicitly approved for deeper
read-only validation. Preserve ADP/market as opponent behavior, availability,
and likely pick timing only. ADP/market must never become NWR private value.

If explicitly approved, create or update a local-only manifest in an ignored
path such as local_exports/mock_draft/manual_input_manifest.local.json. Never
commit the manifest or real CSV files.

Run the Mock Draft readiness checks, report GREEN/YELLOW/RED, list missing
inputs and schema violations, and stop if any real data would be staged or
committed.
```
