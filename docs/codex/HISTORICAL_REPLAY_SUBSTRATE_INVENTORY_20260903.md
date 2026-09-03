# Historical full-season redraft replay — substrate inventory (2026-09-03)

Honest inventory before building anything, per this lane's brief ("If
insufficient: report the missing substrate honestly"). No replay built.

## What exists

- `src/services/historical_draft_service.py` + `tests/test_historical_draft_service.py`:
  loads Yahoo draft exports and handwritten offline notes, extracts only
  the **final 5 picks per season** ("the rookie draft") for one dynasty
  league, 2021-2025 (6 season-records total). Output is pick order/player/
  team only -- no stat production. Never covers veteran rounds.
- `sample_data/historical_yahoo_drafts/final_five_two_seasons.csv` (18
  rows, 2021-2022): a **synthetic test fixture** (4 of 9 rows/season are
  literally `"Keeper Placeholder 2021 A"` etc.), not a real recovered
  export.
- `sample_data/historical_rookie_notes/` (20 + 15 rows, 2022-2025):
  hand-transcribed rookie picks; the 15-row `model_replay_sample.csv` is
  an explicitly synthetic calibration fixture pairing hand-authored
  `model_rank`/`model_score` with realized `outcome_score`.
- `sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv` +
  `post_draft_outcomes.csv` (60 rows each, 2022-2024, 20 rookie prospects/
  season): the most rigorous leakage-safe split in the repo -- every
  pre-draft row's own `source_notes` says "no NFL production used,"
  outcomes are joined only after ranking, stamped
  `future_nfl_stats_used=False` / `ranking_policy=NO_FUTURE_STATS_POLICY`.
  But: **rookie-class evaluation only** (not a snake draft), and the
  "pre-draft" scores are hand-built fixture numbers (`source=
  manual_predraft_fixture`), not an actually-recovered historical
  scouting snapshot.
- `scripts/build_backtest_dataset_v{0,1}.py` + `run_backtest_v{0,1}.py`
  (tested, `tests/test_backtest_*`): a real, working, leakage-guarded
  framework -- but it predicts **player stat production for real NFL
  season S+1 from completed season S**, with a hard leakage guard
  (`BLOCKED_FEATURE_TOKENS`) that explicitly rejects `adp`, `market`,
  `ranking`, `projection`, `fantasy_points` as input features. Real
  backing data (2012-2025, box-score-derived) lives outside the repo at
  `C:\NWR_SHARED_DATA\backtests\...`. **This answers a different question
  than a draft replay** -- it never simulates a snake draft, order, or
  ADP, by design.

## What's missing

- No full prior-season **redraft** snake draft (veterans + rookies, all
  rounds, real pick order) exists anywhere in `sample_data/` for any past
  season. The one file with the right shape --
  `sample_data/kha_real_draft_2026/official_recap_192picks_clean.csv` --
  is the **current 2026** season, not historical.
- No genuinely dated pre-draft ranking/ADP/projection board for a past
  season exists. `pre_draft_prospect_inputs.csv` is the closest analog
  and is rookie-only, synthetic-fixture data.
- The real leakage-guarded backtest framework's blocked-feature list
  (`adp`, `market`, `ranking`, `projection`) means even if historical
  rankings existed, they aren't currently wired to be usable there.

## Verdict

A genuine, leakage-safe **full-season redraft replay** (snake draft with
veterans, scored against what actually happened that real season) is
**not buildable today** from data already in this repo or the reachable
`C:\NWR_SHARED_DATA` tree. To build it, the owner would need to supply,
for at least one past season:

1. the actual full veteran+rookie snake-draft results, pick-by-pick, all
   rounds, all teams -- a real platform export, not a small synthetic
   fixture; and
2. a genuinely dated pre-draft ranking/ADP/projection board captured
   before that draft happened -- not reconstructed after the fact from
   known outcomes.

Until then, the only real, currently-usable replay substrate this lane
has is the 2026 KHA draft itself (`sample_data/kha_real_draft_2026/`) --
which is same-season postmortem evidence, not a leakage-safe prior-season
backtest. The rookie-only historical-draft and pre-draft/outcome
services remain useful for what they were actually built for (calibrating
rookie-pick reconstruction and rookie-class evaluation), and should not
be stretched to stand in for a full redraft backtest they were never
designed to support.
