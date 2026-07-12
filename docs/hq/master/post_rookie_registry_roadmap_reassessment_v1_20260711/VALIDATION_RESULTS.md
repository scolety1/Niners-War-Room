# Validation Results

## Verdict under validation

`GREEN_POST_ROOKIE_REGISTRY_ROADMAP_READY_WITH_SAFE_NEXT_LANE`

## Repository and HQ

| Check | Result | Evidence |
|---|---|---|
| Fetch all remotes | PASS | Completed before worktree creation |
| Direct remote-HQ resolution | PASS | `origin/work/hq-parallel-control` = `794b6cd64ffdc673936d0a1f6c8f4bdfe0fc863e` |
| Expected-HQ match | PASS | Expected and actual hashes are identical |
| Intervening commits | PASS | None; remote advance is zero |
| Isolated branch/worktree | PASS | New branch from verified HQ; existing worktrees untouched |
| Allowed write scope | PASS | All 18 staged files are under the packet prefix |

## Inventory and reconciliation

| Check | Result | Detail |
|---|---|---|
| Current route inventory | PASS | 18 visible, 41 hidden, 59 total route specs, 46 unique page files, zero duplicate URL paths |
| Visible-route list | PASS | Draft Cockpit, Mock Draft, Rankings, Player Compare, Trading Lab, Draft Analyzer, Development Lab and roster/planning tools, Future Tools, Refresh, Evidence Review/Hub, Settings/Data Health |
| Current page inventory | PASS | 46 tracked `app/pages/*.py` files |
| Current service inventory | PASS | 271 tracked `src/services/*.py` files |
| Current test inventory | PASS | 407 tracked `tests/test_*.py` files |
| Existing-roadmap reconciliation | PASS | Old immediate and next-three sequence maps to completed recent lanes and is marked consumed/superseded |
| Recent-lane completion | PASS | Commit sequence from prospective closeout through batch 836e canonical closeout inspected |
| No-recreate contradiction scan | PASS | No selected lane exactly collides with a `DO_NOT_RECREATE` or `BLOCKED` work item; four major blocked families explicitly select `STOP` |
| Classification vocabulary | PASS | All classifications in the five classification matrices use the required vocabulary |
| Candidate selection shape | PASS | Exactly one immediate lane and exactly three ordered later lanes |
| Score formula | PASS | Thirteen weights sum to 100; all 17 weighted scores recomputed within rounding tolerance |

The in-app browser was explicitly invoked for local route inspection. Navigation to `http://localhost:8517` was rejected by the browser security policy, which stated that this local origin must not be used and prohibited workaround or alternate-browser circumvention. No workaround was attempted. For this documentation-only lane, route validation therefore used the navigation registry, its focused tests, and existing rendered AppTest checks. This is a validation-tool caveat, not evidence of an application route defect.

## Governance and pause verification

| Check | Result | Controlling state |
|---|---|---|
| Formula pause | PASS | `PROSPECTIVE_2026_FREEZE_OPERATIONALLY_CLOSED_PENDING_FUTURE_OUTCOMES` |
| Prospective freeze | PASS | PYF, GAUNTLET_081, and current board remain frozen/evaluation-only |
| Flaim pause | PASS | `USEFUL_MANUALLY_NOT_READY_FOR_ADAPTER` |
| FantasyBot pause | PASS | `MANUAL_EXTERNAL_SECOND_OPINION_ONLY` |
| Plugin numerical influence | PASS | `0%` |
| Rookie queue pause | PASS | `ROOKIE_REGISTRY_METADATA_QUEUE_CLOSURE_PAUSED_PENDING_EXACT_CANONICAL_SOURCE_ENDPOINT_EVIDENCE` |
| Rookie reentry metadata | PASS | All eight required elements transcribed; external research/provider contact is explicitly non-triggering |
| External research | PASS | None used; optional ledger correctly omitted |

## CSV and structured-data checks

| Check | Result | Detail |
|---|---|---|
| Spreadsheet-library CSV parse | PASS | All seven CSVs parsed with `Workbook.fromCSV`; row counts are 17, 15, 12, 18, 24, 14, and 18 |
| Independent CSV parse | PASS | All seven CSVs imported successfully with PowerShell `Import-Csv` |
| Duplicate primary keys | PASS | Zero duplicates in candidate, surface, blocker, file-inventory, no-recreate, debt, and gap keys |
| Evidence path existence | PASS | Every repository-like evidence token in the CSV matrices resolves after removing optional line suffixes |
| Packet internal references | PASS | The file inventory matches exactly 18 packet files; all non-optional packet-name references resolve |
| Manifest JSON | PASS | Duplicate-key parse succeeded; 17 non-self hashes/byte counts verified with zero mismatches; self-hash intentionally excluded |

## Focused tests and known baseline evidence

| Command/scope | Result | Interpretation |
|---|---|---|
| Navigation, Data Health, refresh recovery/render, Player Compare, rookie registry/scaffold/linkage/queue, and draft-day Trading Lab service | PASS: `135 passed` | Broad audit-relevant slice passes from a temporary short-path alias |
| Rankings page suites | PASS: `37 passed` | Current ranking page/service expectations in those suites are green |
| Decision Trust Strip rendered AppTest | PASS: `1 passed` | Representative rendered component check is green |
| Trust-banner static baseline | EXPECTED BASELINE: `2 failed, 3 passed` | Both failures inspect thin `app/pages/05_rankings.py` for a literal banner call; no product defect was established and no test was changed |

The first rookie-registry slice attempt from the long worktree path produced two `FileNotFoundError` failures for tracked report paths that exceeded Windows path handling. The identical slice through a temporary short junction passed all 135 tests. This corroborates the already documented Windows long-path validation debt; it did not justify modifying repository content. The temporary junction is removed before delivery. Pytest artifacts are preserved under the repository's existing ignored `.pytest-tmp/` pattern and are absent from the packet inventory and commit.

Existing canonical evidence also records three failures and six skips in an expanded draft slice when ignored local active-pack/history artifacts are absent. This is carried into the technical-debt matrix as a hermetic-fixture issue rather than masked or repaired in this documentation lane.

## Warning and debt inventory

- `use_container_width=True`: 462 static occurrences across 41 app files.
- Existing Refresh/Data Health differential: 11 runtime deprecation messages in the documented smoke path.
- Route specs: 59 over 46 unique files, which confirms alias/wrapper ownership debt.
- Worktrees registered in the controlling clone during audit: 500; no cleanup was attempted.
- No CI workflow or dependency lockfile found.
- `openpyxl` is imported by `src/services/draft_prep_data_foundation_service.py` but absent from `requirements.txt`.

## Protected, frozen, and diff checks

| Check | Result |
|---|---|
| Frozen/freeze/prospective starting-HQ inventory | PASS: 120 files |
| Pre-staging aggregate | PASS: `b6fa2c5c3f7d3fe800e988d7ec9a2bcb39ca7630f2f52008cdab67120bde5d7c` |
| Per-file working bytes vs HEAD checkout-filtered bytes | PASS: 0 mismatches |
| Protected production path changes | PASS: 0 |
| Formula/ranking/source/registry/plugin-governance/draft/data changes | PASS: 0 |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Post-commit frozen rescan | PASS: aggregate unchanged; 0 byte mismatches |
| Clean worktree after local commit | PASS |

## Final seal

CSV, path, manifest, staged-scope, cached-diff, local-commit, post-commit frozen, and clean-worktree checks are complete. The commit is local only and no push was attempted. No implementation has occurred.
