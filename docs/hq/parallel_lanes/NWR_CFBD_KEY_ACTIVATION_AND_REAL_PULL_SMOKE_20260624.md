# NWR CFBD Key Activation and Real Pull Smoke - 2026-06-24

## Final Verdict

YELLOW.

The CFBD connector is now safely configurable from a local key file and the loader no longer reports CFBD as `NOT_CONFIGURED` when `NWR_CFBD_API_KEY_FILE` is set. The real CFBD probe reached the API path but returned `HTTP Error 401: Unauthorized`, so no successful CFBD pull was completed.

## Starting HEAD

`36864ac2cc8285a37b4859bb8477a29307be3e2e`

## Key File Safety Status

- A usable CFBD key value was found in an old local script outside the NWR repo:
  `C:\Users\codex-agent\Documents\New project\scripts\college_football_data\run_cfbd_pipeline.ps1`
- That old folder is a git repo with no commits; the script is untracked there.
- The active NWR repo tracked files were scanned for the extracted key value and returned zero matches.
- The key was not printed.
- The key was not written into docs, logs, `.env`, or tracked files.

## Local Secret Path

The key was copied to:

`C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt`

This path is outside `C:\NWR\Niners-War-Room`.

## Code Support Added

Added `NWR_CFBD_API_KEY_FILE` support:

- `CFBD_API_KEY` environment variable takes precedence.
- If `CFBD_API_KEY` is absent, `NWR_CFBD_API_KEY_FILE` is read at runtime.
- File contents are stripped of whitespace.
- Missing/unreadable key files fail closed to an empty key.
- The key value is never logged by the config layer.

Ignore patterns were also tightened for local key files:

- `*.key`
- `*api_key*.txt`
- `*secret*.txt`

## CFBD Configuration Result

With:

`NWR_CFBD_API_KEY_FILE=C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt`

The refresh registry reported:

- configured: `True`
- loader category: `AUTO_SLOW`
- safe_to_pull: `True`
- required env option: `CFBD_API_KEY or NWR_CFBD_API_KEY_FILE`

## CFBD Real Smoke Result

Command path:

- Full Safe Refresh
- source id: `cfbd_college_football_data`
- write status: `True`

Result:

- overall status: `RED`
- CFBD action: `FAILED`
- CFBD configured: `True`
- CFBD refreshed: `False`
- failure: `HTTP Error 401: Unauthorized`

Interpretation:

The connector/key-file activation path works, but the local key appears invalid, expired, not authorized for the endpoint, or otherwise rejected by CFBD. No model/rank/source-truth files were changed.

## Cache and Status Locations

Raw/cache root:

`C:\NWR_SHARED_DATA\public_sources\cfbd\`

Status manifest written under ignored local exports:

`C:\NWR\Niners-War-Room\local_exports\refresh_data\cfbd\latest\cfbd_refresh_manifest.json`

Tracked artifacts written by CFBD:

None.

## Protected Artifact / Model Guardrails

Confirmed intended behavior:

- CFBD remains review/status only.
- `model_use_allowed` remains false for CFBD review-status behavior.
- CFBD identity-gate warning remains required before model use.
- No refreshed data automatically becomes model/rank input.
- Frozen Final Draft Board V1 was not mutated.
- `final_board_rank` was not changed.
- Dynasty Rank was not changed.
- `latest_candidate` / `latest_approved` were not updated.
- Pinned snapshot was not mutated.

## Tests / Checks

- Focused pytest:
  `tests/test_api_settings.py tests/test_data_refresh_orchestrator_service.py`
  - Result: `22 passed`
- Ruff on touched Python files:
  - Result: passed
- Python compile on touched Python files:
  - Result: passed
- `git diff --check`:
  - Result: passed
- Frozen board row count:
  - Result: `66`
- Pinned hash:
  - Result: matched expected `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- Secret scan of commit-candidate files:
  - Result: zero matches
- Tracked CFBD/cache/shared artifacts:
  - Result: no CFBD secret/cache/raw output files added

## Remaining Risks / Gaps

- The local key should be checked in the CFBD account or rotated because the API returned 401.
- The old untracked local script contains a literal key assignment. It is outside the NWR repo and untracked, but the safer long-term cleanup is to remove the literal secret from that script and rely on `C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt`.
- A full successful CFBD pull is still pending a valid/authorized key.
