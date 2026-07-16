# Focused and Broader Results

| Gate | Result | Exit code | Skips / xfails |
|---|---:|---:|---:|
| Exact original nine | 9 passed | 0 | 0 / 0 |
| Required negative controls | 16 passed, 10 deselected | 0 | 0 / 0 |
| Complete three changed test files | 32 passed | 0 | 0 / 0 |
| Owning and adjacent regression | 116 passed, 14 skipped | 0 | 14 / 0 |
| Accessibility and presentation | 35 passed | 0 | 0 / 0 |
| Disposable mutation rerun | 16 passed, 10 deselected | 0 | 0 / 0 |

The owning/adjacent selection covered the Phase-5 display contract, Player
Board, trust banners, current and legacy Dynasty Rankings, Draft Prep, Draft
Room checklist, Decision Trust Strip service/surfaces/rendering, navigation,
Player Board score/value, and trust status.

The fourteen skips are unchanged missing-LocalData sentinels in
`test_player_board_score_service.py`; no focused or negative-control node is
skipped or xfailed. No skip or xfail marker was added.

Static results:

- `compileall app src tests`: pass.
- Ruff on all four changed Python paths: zero findings.
- Full Ruff differential: starting HQ `81`, candidate `80`, zero new findings.
- `git diff --check`: pass.
- Pre-packet `git diff --cached --check`: pass.
