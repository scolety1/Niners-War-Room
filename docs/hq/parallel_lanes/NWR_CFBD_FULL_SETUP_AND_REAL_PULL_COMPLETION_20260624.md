# NWR CFBD Full Setup and Real Pull Completion - 2026-06-24

## Final Verdict

RED for CFBD pull completion.

Secret handling and key-file configuration are safe, but the direct CFBD auth smoke returned `401 Unauthorized`. Per the handoff, the broad Full Safe Refresh pull was not run after direct auth failed.

## Starting HEAD

`b6554d22d6ac68c771c315d457e123ce3e7ac916`

## Repo / Branch

- Repo: `C:\NWR\Niners-War-Room`
- Branch: `work/hq-parallel-control`
- Initial status: clean and synced with `origin/work/hq-parallel-control`

## Local Secret File

- Expected path: `C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt`
- Exists: yes
- Tracked by active NWR repo: no; path is outside the repository
- Trimmed length: `19`
- Masked suffix: `****here`
- Contains labels such as `CFBD_API_KEY=`: no
- Contains surrounding quotes: no
- Contains extra whitespace/newline: yes

The key value was not printed, logged, committed, or written into this report.

## Direct Auth Smoke

- Auth method: `Authorization: Bearer <local key>`
- Endpoint category: minimal CFBD FBS teams probe
- HTTP status: `401`
- Result class: `HTTP_ERROR`
- Reason: `Unauthorized`

Interpretation:

The connector can read the local secret file and construct an authenticated request, but CFBD rejected the supplied key. The masked suffix and short length suggest the file may still contain placeholder text or an unauthorized token. The next step is to replace/rotate the key with a valid CFBD API token, save the file, and rerun this smoke.

## Full Safe Refresh Result

Not run in this pass.

Reason: the handoff explicitly says to stop before broad pulls if direct auth returns `401`.

Prior key-file activation work already proved that the loader reports CFBD as configured when `NWR_CFBD_API_KEY_FILE` points to a readable local secret file. This pass did not advance to a successful CFBD refresh because direct auth failed.

## Cache Location

Expected raw/cache location remains:

`C:\NWR_SHARED_DATA\public_sources\cfbd\`

No new successful CFBD raw payload was produced by this pass.

## Review Artifacts

Because auth failed before a successful pull:

- `cfbd_review_status.csv`: not newly produced by this pass
- `cfbd_identity_review_queue.csv`: not produced
- `cfbd_coverage_report.csv`: not produced
- `cfbd_data_dictionary.csv`: not produced

Required review-only policy remains:

- `model_use_allowed=false`
- `identity_review_required=true`
- `training_allowed=false`

## Secret / Cache Tracking Proof

- Local secret path is outside the repo.
- The key value was not printed.
- The key value was not added to tracked files.
- No `.env` file was committed.
- No `C:\NWR_SHARED_DATA` files were tracked.
- No raw CFBD cache files were tracked.

## Guardrail Confirmation

Confirmed:

- Frozen Final Draft Board V1 was not mutated.
- `final_board_rank` values were not changed.
- Dynasty Rank was not overwritten.
- `latest_candidate` / `latest_approved` were not updated.
- Pinned snapshot hash remained unchanged.
- Production model/rank logic was not changed.
- CFBD data did not become model input.
- No candidate/model/rank outputs were written.
- Gmail/vendor/RotoWire were not scraped.

## Tests / Checks

- Focused pytest for API settings and refresh orchestrator: passed.
- Ruff on touched Python files: passed in prior key-file activation commit; no Python files were changed in this pass.
- Python compile on touched Python files: passed in prior key-file activation commit; no Python files were changed in this pass.
- `git diff --check`: passed.
- Frozen board row count: `66`.
- Pinned hash: unchanged.
- Tracked shared/cache/secret scan: clean.

## Remaining Blocker

CFBD cannot complete a real pull until a valid API key is saved at:

`C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt`

After replacing the key, rerun the direct auth smoke first. If it returns HTTP 200, then run Full Safe Refresh and produce the review/status artifacts.

