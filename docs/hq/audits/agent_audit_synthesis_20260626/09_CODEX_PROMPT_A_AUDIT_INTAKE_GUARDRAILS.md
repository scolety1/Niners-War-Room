# Codex Prompt A — NWR Audit Intake + Guardrail Validation Lane

You are working on Niners War Room. Use this prompt exactly.

## Goal

Ingest the consolidated six-agent audit synthesis as review/audit infrastructure and add guardrail validation. Do not implement broad product features yet.

## Starting point

Latest confirmed Master:

- Branch: `work/hq-parallel-control`
- HEAD: `16b78728cc11a66ba335308f028acf223002ca4a`
- Status from last report: clean/synced with origin

Use an isolated worktree/branch. Do not assume `C:\NWR\Niners-War-Room` is safe for editing if another lane is active.

Recommended branch/worktree name:

- `work/hq-agent-audit-intake-20260626`
- `C:\NWR\Niners-War-Room-agent-audit-intake-20260626`

## Inputs

Use the HQ handoff packet files:

- `00_START_HERE_CODEX.md`
- `01_HQ_AUDIT_SYNTHESIS.md`
- `02_CONSOLIDATED_CODEX_ACTION_MATRIX.csv`
- `04_DATA_MODEL_GUARDRAILS.md`
- `05_CFBD_REVIEW_ONLY_SYNTHESIS.md`
- `08_VALIDATION_AND_SOURCE_INVENTORY.md`
- `source_inventory_69_files.csv`
- `source_zip_manifest.csv`
- raw source zips only as evidence, not current instructions

## Required tasks

1. Create a review/audit folder, for example:
   `docs/hq/audits/agent_audit_synthesis_20260626/`

2. Copy the consolidated HQ synthesis files into that folder.

3. Add or update validation tests for:
   - CFBD Agent 1/2/3 review-only flags.
   - Agent3 final decision counts: APPROVE=4, KEEP_BLOCKED=8, NEEDS_MORE_INFO=3.
   - No row has `approved_by_human=true`, `model_use_allowed=true`, or `training_allowed=true`.
   - No blocked evidence fields are present in model feature manifests or production rank logic.
   - Missing age/status/injury/outcome/player_id is not coerced to zero/clean/average.
   - Raw/shared/local/secret/vendor/Gmail/cache files are not tracked.
   - Protected artifacts were not modified.

4. Record parse warnings for malformed audit CSVs. Do not blindly import malformed whole-project CSVs into app data.

5. Add or update a local preflight/checklist if one already exists. Otherwise create a small docs-only checklist and a lightweight test script where appropriate.

## Guardrails

Do not mutate:

- Frozen Final Draft Board V1
- `final_board_rank`
- Dynasty Rank
- tier assignments
- pinned snapshot
- `latest_candidate`
- `latest_approved`
- production model/rank logic
- source-truth/model-input gates

Do not promote:

- CFBD
- NFL usage
- Gmail
- vendor/RotoWire/FantasyPros
- proxy/inferred historical data
- Outcome probabilities
- DynastyProcess/ADP/market values

Do not track:

- `C:\NWR_SHARED_DATA`
- `C:\NWR_LOCAL_SECRETS`
- `local_exports`
- raw cache/API/vendor/Gmail files
- secrets or API keys

Hosted deployment remains blocked.

## Validation to run

Run the repo’s standard checks, at minimum:

- `python -m pytest`
- `python -m ruff check .` if available
- any existing protected-artifact / raw-data / guardrail tests
- new tests added in this lane

## Final response format

Return:

1. Branch/worktree used.
2. Commit hash.
3. Files changed.
4. Tests run and results.
5. Exact validation of guardrails.
6. Confirmation that no model/rank/source-truth/pinned/latest/frozen artifacts were modified.
7. Any parse warnings or unresolved audit import caveats.
