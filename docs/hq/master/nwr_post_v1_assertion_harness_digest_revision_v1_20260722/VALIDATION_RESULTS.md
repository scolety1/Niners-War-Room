# Validation results

- Starting remote HQ/tree: exact expected values after fetch/prune.
- Source commits and parents: exact linear chain.
- Source worktree: clean at `18c63e96`; rejected worktree: clean at `c4d52d72`.
- Original blockers: reproduced before revision.
- Focused harness/route/digest suite: 36 passed.
- Workflow negative controls: 7 of 7 detected, including contradiction.
- Page-open negative controls: 6 of 6 detected.
- Normal Start Here durable mutation count: `0`.
- Session-only mutation durable mutation count: `0`.
- Digest contract edge cases: all passed.
- Persistent inventory: 14 files / 542,801 bytes; Digest V1 reproducible.
- Recovery inventory: 7 files / 172,878 bytes; Digest V1 reproducible.
- Legacy aggregates: `LEGACY_AGGREGATE_METHOD_NOT_REPRODUCIBLE`.
- Application source changes: none.
- Production ranking change: `NONE`.
- Primary five opaque CSV hashes: exact.
- Protected/frozen unauthorized changes: zero.
- Required verdict: `GREEN_NWR_POST_V1_ASSERTION_HARNESS_REVISION_READY_FOR_ADOPTION`.
