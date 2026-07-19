# Hermetic and LocalData results

## Hermetic

The full gate ran in a clean disposable checkout whose tree exactly matched the staged candidate tree.

- Bootstrap: 13/13.
- Security: 20/20.
- Python: 2,648 passed.
- New skips: 0.
- New xfails: 0.
- New xpasses: 0.
- Exit code: 0.

An earlier diagnostic invocation in the intentionally staged source worktree reached 2,638 passed and 10 lane-state assertion failures because those historical tests require no staged `app/` changes. The controlling clean exact-candidate run above resolves that environmental mismatch and is the release result; no product test was removed or weakened.

## LocalData

Status: `BLOCKED_MISSING_LOCAL_TEST_PACK`.

Exit code: 4.

LocalData is not counted as passed or skipped. No local data files were inspected, copied, restored, normalized, staged, or committed.
