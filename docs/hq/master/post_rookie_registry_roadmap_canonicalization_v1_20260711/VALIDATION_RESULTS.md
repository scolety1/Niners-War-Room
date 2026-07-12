# Validation Results

## Repository and ancestry

- Fetch all remotes: PASS.
- Verified live HQ: `794b6cd64ffdc673936d0a1f6c8f4bdfe0fc863e`.
- Remote advance from expected HQ: none.
- Source commit: `19282aebe5e3bd6d203afc1afdc7056aaa714b0c`.
- Source parent and merge base: verified live HQ.
- Isolated review worktree: PASS.

## Source packet

- Source files: 18.
- Documentation CSVs: 7.
- All changed paths inside source packet: PASS.
- Source manifest duplicate JSON keys: 0.
- Source manifest non-self entries: 17.
- Source manifest hash/byte mismatches in untouched source worktree: 0.
- Source manifest hash/byte mismatches against immutable commit blobs: 0.
- CSV parsing failures: 0.
- Duplicate primary keys: 0.
- Candidate score recomputation mismatches: 0.
- Immediate selection shape: one immediate lane.
- Later selection shape: three ordered lanes.
- No-recreate, parked-item, and reentry-trigger consistency: PASS.

## Tests and baselines

The exact audit slice covering navigation, Data Health, refresh recovery/render, Player Compare, rookie registry/scaffold/linkage/queue, and draft-day Trading Lab service passed: `135 passed`.

The trust-banner static baseline reproduced exactly: `2 failed, 3 passed`. The failures remain confined to literal-text expectations against `app/pages/05_rankings.py`; no related test or application file changed.

## Figures

| Figure | Reproduced result |
|---|---:|
| Source packet files | 18 |
| Focused tests | 135 passed |
| Documentation CSVs | 7 |
| Protected production-path changes | 0 |
| Frozen starting-HQ inventory | 120 files |
| Frozen byte mismatches | 0 |
| Implementation changes | 0 |

## Trading Lab and governance

- Existing manual selection, scenario construction, notes, checklists, memo/CSV export, trust context, and session state: confirmed.
- Existing Trading Lab persistence: none.
- Automated valuation, fairness verdict, winner, offer generation, and recommendation: absent and test-prohibited.
- Existing reusable persistence lifecycle: confirmed in Development Lab state service.
- Formula/plugin/rookie/source/frozen pauses preserved: PASS.

## Final checks required after commit

- Adoption manifest and inventory hashes.
- `git diff --check` and `git diff --cached --check`.
- Final protected/frozen rescan.
- Normal non-force push.
- Remote readback at the adoption commit.
- `0 ahead / 0 behind` and clean worktree.
