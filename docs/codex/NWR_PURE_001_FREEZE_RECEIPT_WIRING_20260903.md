# NWR PURE 001 freeze receipt — real repo-state wiring (section 27)

Code: `src/services/nwr_pure_experiment_service.py`
(`build_git_provenance`, `build_freeze_receipt_from_repo_state`). Tests:
`tests/test_nwr_pure_experiment_service.py`, 19/19 passing (5 new).

## What's real and working

`build_git_provenance(repo_root)` shells out to real `git` (branch,
HEAD, and the HEAD tree object hash, plus `git status --porcelain` to
detect a dirty tree) and returns real values — no field is ever
fabricated; anything it cannot determine (git unavailable, not a
repository) comes back `"UNKNOWN"` explicitly. Verified in-session
against this actual worktree:

```
app_branch: work/nwr-draft-upgrade-hq-v1-20260903
app_head:   5d6e9b414b65545d73d948e6d58a315660e9a477
app_tree:   8bc4229b60115650d4edf6713714152601b62642+UNCOMMITTED_CHANGES:23d50881...
```

(`app_head` matches the actual last commit at the time this was run; the
`+UNCOMMITTED_CHANGES:` suffix correctly appeared because this section's
own new files were still uncommitted at that moment — the dirty-state
detection is doing real work, not a placeholder.)

`build_freeze_receipt_from_repo_state(...)` assembles a complete, real
`ExperimentFreezeReceipt` from that git provenance plus an already-
computed `RankingResult` (`model_sha` = `ranking.projection_sha256`,
`source_as_of` = `ranking.generated_at_utc`), an already-hashed league
profile document, and caller-supplied player-universe approval fields
(`player_universe_sha`/`row_count`/`valid_until` — sourced from the
governed manifest/approval receipt by the caller; this function does not
re-validate the player universe itself, that gate already lives in
`redraft_engine_v1_service.py`). `algorithm_version`/`authority_label`
come from the real `MODEL_FAMILY`/`REDRAFT_AUTHORITY_LABEL` constants;
`team_score_version`/`championship_equity_version`/`pick_score_version`
default to the real version constants in
`shadow_numeric_authorities_service.py`. It does not itself call
`freeze_experiment()` — the caller decides whether and when to commit
the freeze, same as every other explicit-action gate this session has
built (Champion/Challenger's `record_promotion_decision`, the catch-up
paste's apply-only-when-ready gate).

## What remains blocked

Producing an actual `NWR_PURE_001_FREEZE_RECEIPT.json` for a live
experiment needs a real, currently-governed `RankingResult` and player-
universe approval — the same Saturday player-universe hard gate
established earlier this session as genuinely blocked in this
environment (no in-repo mechanism can produce a validly-approved fresh
snapshot without real current NFL data and explicit owner approval). This
wiring is real and ready; invoking it end-to-end for an actual frozen
experiment is not fabricated here, because doing so would require either
a fake ranking (explicitly against this session's rules) or a real
governed snapshot that does not exist in this environment right now.
