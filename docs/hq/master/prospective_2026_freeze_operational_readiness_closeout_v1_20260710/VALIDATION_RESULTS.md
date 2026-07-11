# Validation Results

## Canonical verification

- Live HQ: PASS — `origin/work/hq-parallel-control` resolved to `e4693f49fa44dba6e75b488d6a560a88ea715b8d`; no advance.
- Canonical path and commit: PASS.
- Preregistration SHA-256: PASS — `1b8cfac3807613c453588a60b24b6303e8bcaac35d03639c1927ec8d81735e28`.
- Baseline freeze SHA-256: PASS — `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`.
- Canonical manifest entries: PASS — 30 non-manifest entries, including intentional challenger absence.
- Input/source receipts: PASS — all 10 recorded receipts resolved and matched.
- Prediction-record hashes: PASS — 924/924 reproduced using the frozen typed schema.
- Freeze timestamps, candidate IDs, formula versions, cutoffs and source dates: PASS.

## Structure, semantics and coverage

- Required columns and data types: PASS.
- CSV parsing: PASS — nine closeout CSVs parsed; canonical CSVs were read without mutation.
- Duplicate comparator/player/position keys: PASS — zero.
- Numeric valid scores and reasoned invalid scores: PASS.
- Score direction, ordinal ranks, tie-break policy and coherent sequences: PASS.
- Position coverage: PASS — formula comparators support QB/RB/WR/TE; current board separately preserves eight unsupported K rows.
- PYF: PASS — 342 preserved / 231 valid / 111 explicitly null-fenced.
- GAUNTLET_081: PASS — 342 preserved / 231 valid / 111 explicitly null-fenced.
- Current board: PASS — 240 preserved / 232 valid / eight explicitly invalid K rows.
- Identity: PASS — admitted comparator identities populated; no normalized-name controlling join.
- Rejected challenger: PASS — no ridge rows and no challenger-freeze file.
- Potential freeze defects: none.

## Operational readiness

- Outcome contract: READY WITH NARROW PRE-OUTCOME ADDENDUM; canonical contract unchanged.
- Append-only tracking: PASS.
- Recovery without old worktrees, ZIPs, chat history or untracked files: PASS.
- Internal paths: PASS.
- Contradictory-language scan: PASS.

## Repository gates

- Allowed write scope: PASS — only this closeout packet.
- Canonical frozen-path byte-change scan: PASS — no canonical path changed.
- Production/ranking/formula/app/source/recommendation/sort diff: PASS — none.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS before staging; rerun after staging.
- Push authorization: conditional on final remote recheck after local commit.

Clean-worktree and final remote checks are performed after the local closeout commit.
