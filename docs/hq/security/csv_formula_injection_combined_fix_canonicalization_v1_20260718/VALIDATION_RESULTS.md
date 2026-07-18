# Validation Results

## Git and sealed evidence

| Gate | Result | Exit |
|---|---:|---:|
| Fetch/prune all remotes | pass | 0 |
| Starting live HQ | `46d0f40eb5f1b00a7a993ed90958d37461aaa1b5` | 0 |
| Starting live HQ tree | `487797f692ec132ad32c95044fdb810cfc3e33a1` | 0 |
| Remote advance | none | 0 |
| Original commit direct parent | exact | 0 |
| Correction commit direct parent | exact | 0 |
| Candidate branch | clean at exact correction commit | 0 |
| Sealed scan target | exact combined base/head | 0 |
| Sealed scan finalization | completed and sealed | 0 |
| Sealed artifact hashes | `30/30` | 0 |
| Coverage / reportable findings | complete / zero | 0 |

## Focused behavior

| Gate | Result | Exit |
|---|---:|---:|
| Combined real-boundary nodes | `170 passed` | 0 |
| Development Lab selection | `85 passed, 85 deselected` | 0 |
| Draft Freeze selection | `85 passed, 85 deselected` | 0 |
| Draft Freeze board families | `9 passed` | 0 |
| Semantic mutation nodes | `10 passed` | 0 |
| Complete focused regression file | `272 passed` | 0 |
| Owning and adjacent export suite | `334 passed` | 0 |
| Exact tracked UI contract | `9 passed` | 0 |

The 334-node suite is the complete focused file plus
`test_draft_freeze_service.py`, the Development Lab state/review/NFLVerse
context services, `test_future_tools_rd_service.py`,
`test_display_only_ngs_context_service.py`, and `test_league_service.py`.

The exact UI set is all six Phase-5 display-language nodes, the routed Player
Board label contract, and the two primary trust-banner contracts.

## Repository tiers and static gates

| Gate | Result | Exit |
|---|---:|---:|
| Hermetic bootstrap | `13/13` | 0 |
| Hermetic security controls | `20/20` | 0 |
| Hermetic Python | `2513 passed` | 0 |
| Hermetic skip/xfail/xpass | `0/0/0` | 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`; zero collected | 4 captured |
| Python compilation over `app`, `src`, `tests` | pass | 0 |
| Four changed Python files Ruff | pass | 0 |
| Full Ruff differential | `4443 -> 4443`; zero new | legacy nonzero |
| Original required-file manifest | `8/8` present | 0 |
| Correction Git-blob manifest | `18/18` indexed hashes/bytes | 0 |
| Changed JSON / CSV parse | `2/2` JSON; `7/7` CSV | 0 |
| Exact path whitelist | `31/31`; zero unexpected | 0 |
| Security automation | zero changed paths | 0 |
| Protected/frozen paths | zero matches | 0 |
| `git diff --check` | pass | 0 |
| `git diff --cached --check` before staging | pass | 0 |
| Primary preservation | five exact SHA-256 matches | 0 |

The correction manifest is validated against committed Git blob bytes because
Windows checkout line-ending conversion is not the canonical artifact identity.
No new security scan was run. No LocalData result is counted as a pass, skip,
xfail, xpass, or Hermetic execution.
