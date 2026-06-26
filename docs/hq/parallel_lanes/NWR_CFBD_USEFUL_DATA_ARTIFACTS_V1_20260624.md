# NWR CFBD Useful Data Artifacts V1 - 2026-06-24

## Verdict

GREEN for review-only artifact creation.

CFBD auth, safe key-file support, raw outside-git caching, and tracked review artifacts are working. CFBD data remains review-only and is not model input.

## Starting HEAD

`c7583300dd3652723e7c916cc8121dbc94b31bf4`

## Branch / Worktree

- Branch: `codex/cfbd-useful-data-artifacts-v1-20260624`
- Worktree: `C:\NWR\Niners-War-Room-cfbd-useful-data-v1`
- Base: `origin/work/hq-parallel-control`

## CFBD Auth / Key Status

- Local key-file support confirmed through `NWR_CFBD_API_KEY_FILE`.
- Safe metadata only was printed: configured true, API base, and file-exists status.
- The CFBD key value was not printed, logged, written to artifacts, or committed.
- Direct shape smoke returned HTTP 200 for `teams/fbs`, team-scoped `roster`, `stats/player/season`, and `recruiting/players`.

## Endpoints Attempted

- `/teams/fbs?year={season}`
- `/stats/player/season?year={season}&category={passing|rushing|receiving}`
- `/recruiting/players?year={season}`
- `/roster?year={season}&team={school}`

The all-roster shape query `/roster?year=2026` returned 0 rows, so roster identity V1 uses team-scoped pulls.

## Successful Datasets / Seasons

Final run ID:

`cfbd_review_artifacts_v1_20260624_20260626T075428Z`

Raw cache location:

`C:\NWR_SHARED_DATA\public_sources\cfbd\cfbd_review_artifacts_v1_20260624_20260626T075428Z`

| Dataset | 2024 rows | 2025 rows | 2026 rows |
|---|---:|---:|---:|
| FBS teams | 134 | 136 | 138 |
| Roster player identity | 16,221 | 15,601 | 0 |
| Passing player season stats | 7,147 | 7,497 | 0 |
| Rushing player season stats | 15,950 | 16,590 | 0 |
| Receiving player season stats | 20,435 | 21,255 | 0 |
| Optional recruiting players | 2,548 | 2,507 | 3,107 |

## Artifacts Created

Tracked under `docs/hq/data_sources/cfbd_review_artifacts_20260624/`:

- `README.md`
- `cfbd_pull_manifest.csv`
- `cfbd_player_identity_review_queue.csv`
- `cfbd_player_production_review.csv`
- `cfbd_coverage_report.csv`
- `cfbd_data_dictionary.csv`

## Identity Review Queue Status

- Rows: 31,822
- Seasons covered: 2024 and 2025 roster rows
- 2026 roster rows: 0 from CFBD at run time
- NWR/Sleeper candidates: intentionally blank
- Match status: `unmatched_review_required`
- Guardrails: `model_use_allowed=false`, `training_allowed=false`, `identity_review_required=true`, `review_only=true`

## Production Review Status

- Rows: 16,938 grouped player/category production review rows
- Seasons covered: 2024 and 2025
- Categories: passing, rushing, receiving
- 2026 production rows: 0 from CFBD at run time
- Guardrails: `model_use_allowed=false`, `training_allowed=false`, `identity_review_required=true`, `review_only=true`

## Coverage Gaps

- 2026 roster identity returned 0 rows.
- 2026 passing/rushing/receiving player season stats returned 0 rows.
- Optional recruiting data was cached and counted for coverage only; no tracked recruiting detail artifact was promoted in V1.
- Roster identity rows require manual identity matching before any NWR/Sleeper linkage.

## Guardrail Confirmation

Confirmed:

- CFBD artifacts are review-only and not model input.
- No candidate/model/rank outputs were written.
- No rankings, final board ranks, tiers, Dynasty Rank, latest candidate, latest approved, or pinned snapshot were changed.
- No nflverse logic was changed.
- No Full Safe Data Loader modes or architecture were changed.
- No Gmail, vendor, RotoWire, DynastyProcess market baseline, or NFL data-loader lane work was touched.
- Raw CFBD cache files remain outside git under `C:\NWR_SHARED_DATA\public_sources\cfbd\`.
- Local secrets remain outside git under `C:\NWR_LOCAL_SECRETS\`.

## Tests / Checks

- Focused pytest added for CFBD review artifact helpers.
- CSV load validation completed for all tracked CSVs.
- Required columns validated for all tracked CSVs.
- Review-only flags validated:
  - `model_use_allowed=false`
  - `training_allowed=false`
  - `identity_review_required=true`
  - `review_only=true`
- Raw cache and local secret tracking scans completed.
- Frozen board row count checked at 66.
- Pinned hash checked unchanged.
- `latest_candidate` / `latest_approved` checked untouched.
- `git diff --check` completed.

## Remaining CFBD V2 Work

- Add a resumable roster cache merge so future rate-limited team pulls can reuse prior successful team payloads.
- Add a dedicated recruiting review artifact only after identity-link rules are defined.
- Add reviewed CFBD-to-NWR/Sleeper identity matching workflow.
- Add endpoint-specific coverage thresholds and expected-team reconciliation.
- Keep all CFBD fields behind review gates until a separate promotion/backtest lane approves them.
