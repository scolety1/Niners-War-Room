# NWR V1 RC1 final runtime revision report

Verdict: `GREEN_NWR_V1_RC1_RUNTIME_MANIFEST_REVISION_READY_FOR_FINAL_ADOPTION`.

This successor is based directly on RC commit `c380956dcab863dd7f921ec237506c08f46990b8`, whose parent is canonical HQ `7a3d01a5fdd95f4a71d49ced7ff00b334434aa73` and whose canonical HQ tree is `b4ab40e584c7c1d39d00f93ee8e5725dc22aafdf`. The current branch is `work/nwr-v1-rc1-runtime-targeted-revision-v1-20260718`. No push occurred.

The original 24-path route/runtime candidate was preserved. The only implementation correction in this authorized pass changes the Data Health runtime-JSON guardrail from a path-substring rule to normalized path ownership plus the prior fail-closed runtime-name fallback. The exact prior RED packet under `docs/hq/master/nwr_v1_rc1_runtime_targeted_revision_v1_20260718/` remains byte-for-byte unchanged.

The classifier consumes repository-relative `git ls-files` output. Canonical `docs/hq` metadata named `MANIFEST.json`, `manifest.json`, `metadata.json`, or `receipt.json` is documentation rather than runtime state. Exact ignored operational roots `local_exports/`, `draft_runtime_state/`, and `draft_day_runtime/`, plus the service-owned `C:\NWR_SHARED_DATA\draft_runtime_state` root, retain runtime authority. Unknown JSON paths still fail closed when their normalized path contains `runtime` or `draft_log`. Windows/POSIX separators, case folding, dot segments, traversal, and lookalike roots are covered by focused tests.

Pre-commit evidence is green: classifier/Data Health 34/34 and broad Data Health 142/142; route/lifecycle/accessibility 63/63; CSV/trust security 339/339; tracked UI contract 26/26; security automation 20/20; full clean-tree Hermetic bootstrap 13/13, security 20/20, and Python 2,648/2,648, exit 0; LocalData `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4; endpoint matrix 180/180; and three runtime cycles with 180/180, 34/34, and 34/34 browser checks plus three successful second starts. All fatal markers were absent, browsers closed before shutdown triggers, all shutdowns exited zero without forced cleanup, and port 8520 was released.

The lifecycle result remains `BOUNDED_WINDOWS_PROCESS_LIFECYCLE_MITIGATION_VALIDATED_BY_REPEAT_RUNS`. It does not claim that the external CPython handle owner was proven.

The immutable successor packet records pre-commit evidence. Exact-tree post-commit verification is intentionally performed after the one allowed successor commit and is reported in the final adoption response; the commit must not be amended if that verification fails.
