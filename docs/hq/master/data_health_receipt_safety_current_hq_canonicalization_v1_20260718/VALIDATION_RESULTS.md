# Validation Results

| Gate | Result | Evidence |
|---|---:|---|
| Canonical remote preflight | PASS | 9c023e20a6bc491f9149da9be6c88fcd5bc09d0b tree 103b9a8a7868fe26a704ec2abf5151c09846ee3a |
| Historical ancestry | PASS | 6bcb9c3 to e94960f to 5b866fc verified |
| Rejected review isolation | PASS | 559985e not adopted or cherry-picked |
| Compatibility map | PASS | 56 paths; 15 clean net; 41 documentation only; zero post-base overlaps |
| Exact final-net transplant | PASS | 56 expected and actual paths; zero missing or extra paths |
| Focused receipt safety | PASS | 72 passed |
| Inherited receipt and Data Health regression | PASS | 87 passed |
| Route smoke | PASS | 2 passed |
| Page-open no mutation | PASS | 14 passed |
| Orchestrator | PASS | 19 passed |
| Refresh Recovery | PASS | 5 passed |
| Decision Trust including negation security | PASS | 38 passed |
| CSV formula security | PASS | 272 passed |
| Tracked UI gate | PASS | 9 passed |
| Navigation | PASS | 17 passed |
| Compact width | PASS | 33 passed |
| Settings and Data Health | PASS | 13 passed |
| Changed Python compile | PASS | 15 changed Python paths compiled |
| Changed-path Ruff | PASS | All checks passed |
| Full Ruff differential | PASS | 4443 baseline and 4443 candidate; zero new findings |
| Historical evidence packets | PASS | Strict JSON duplicate-key CSV and render checks passed |
| Strict Hermetic implementation gate | PASS | bootstrap 13; security 20; Python 2613; Ruff pass; exit 0 |
| LocalData | BLOCKED | BLOCKED_MISSING_LOCAL_TEST_PACK; exit 4; not passed or skipped |
| Formula-chain protection | PASS | 46 of 46 paths blob-identical |
| Protected current-HQ paths | PASS | 9 of 9 explicit blobs identical |
| Primary worktree preservation | PASS | exactly five modifications; all five SHA-256 hashes matched |
| Storage boundary | PASS | ignored local-only root; zero tracked receipt artifacts |
| Independent read-only review | PASS | 18 of 18 questions green; zero unresolved findings |
| Canonical packet shape | PASS | exactly 19 required documentation files |

Before normal push, validation requires a strict packet parse, a documentation-only staged diff, a strict Hermetic repeat from the final candidate content, a separate LocalData exit-4 capture, and a final fetch proving the remote still has the controlling HQ commit and tree.
