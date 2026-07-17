# Validation Results

## Applicability and buildability

| Gate | Result | Exit |
|---|---:|---:|
| Remote fetch/prune | pass | 0 |
| Canonical HQ/tree | exact match | 0 |
| Candidate direct-child relation | one commit; exact parent | 0 |
| Candidate worktree cleanliness | clean | 0 |
| Python compilation | pass | 0 |
| Changed-file Ruff | pass | 0 |
| Repository Ruff differential | `4443 -> 4443`; zero new | legacy nonzero |

## Security closure

| Gate | Result | Exit |
|---|---:|---:|
| Exact pre-fix scan replay | `50/58`; eight reproduced failures | 0 harness |
| Exact post-fix scan replay | `58/58` | 0 |
| Expanded real-boundary matrix | `112/112` | 0 |
| Combined real-boundary adversarial executions | `170/170` | 0 |
| Semantic mutation controls | `10/10 detected` | 0 |
| CR / LF / NBSP / mixed | all pass on both surfaces | 0 |
| Index-zero marker / exact suffix | pass | 0 |
| Behavioral idempotence | pass | 0 |

## Preserved behavior

| Gate | Result | Exit |
|---|---:|---:|
| Direct helper and related focused file | `272 passed` | 0 |
| Owning and adjacent focused suite | `334 passed` | 0 |
| Draft Freeze named board families | `9/9` | 0 |
| Typed identity and exact type | pass | 0 |
| CSV structure and content | pass | 0 |
| Alternate bypass review | no affected bypass | n/a |

## Repository gates

| Gate | Result | Exit |
|---|---:|---:|
| Hermetic bootstrap controls | `13/13` | 0 |
| Hermetic security controls | `20/20` | 0 |
| Hermetic Python collection | `2513 passed` | 0 |
| Tracked UI contract | `9 passed` | 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`; zero collected | 4 captured |
| Security automation diff | no changes | 0 |
| Protected/frozen scan | zero matches | 0 |
| `git diff --check` | pass | 0 |
| `git diff --cached --check` | pass | 0 |
| Primary-worktree hashes | five exact matches | 0 |
| Independent targeted review | no unresolved finding | 0 |

No new skip, xfail, or xpass was introduced. No LocalData result was counted as
Hermetic validation.
