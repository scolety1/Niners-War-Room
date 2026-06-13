# Rookie Shadow Ranking Audit - 2026-06-13

## Verdict

GREEN.

The Rookie Framework v0.3 shadow ranking export is safe as a shadow/export-only artifact. It does not create production rankings, private scores, rookie probabilities, probability bands, app-readable outputs, outcome columns, or veteran outcome-head inputs.

## Blockers

None.

## Warnings

- The 5.04 shadow output separates capped players from uncapped watchlist rows, but the shadow CSV does not carry `tag_summary`. That means asymmetric-role rationale is inherited from Step 2 review-board context rather than visible in each Step 3 row. This is not a blocker because `review_bucket`, `review_status`, hard caps, manual flags, gaps, source confidence, and notes remain visible; however, Step 5 should consider a patch queue item to carry role/tag rationale into the shadow export before any user-facing packet.
- Pytest is unavailable in both available Python runtimes. The direct Step 3 test harness passed all tests.
- Prohibited terms such as `adp`, `ranking`, and `projection` appear only in `prohibited_sources_detected` warning fields. They are not private-value inputs.

## Source-Safety Review

The shadow builder reads Step 2 review-board local exports only:

- `rookie_review_board_v03.csv`
- `rookie_review_board_premium_review_v03.csv`
- `rookie_review_board_round2_v03.csv`
- `rookie_review_board_5_04_watchlist_v03.csv`
- `rookie_review_board_manual_flags_v03.csv`
- `rookie_review_board_remaining_gaps_v03.csv`
- `README_ROOKIE_REVIEW_BOARD_V03.md`

It writes only to `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`.

Strict mode rejects prohibited private-value input columns, including ADP, rank/ranking, projections, consensus, market/trade value, `private_score`, probability, and band fields. The only allowed warning field is `prohibited_sources_detected`, which remains quarantined as a warning.

Secondary-source charting remains in soft/manual context through Step 2 fields. Scouting prose and injury notes remain manual-review context and are not converted into numeric grades.

## Premium Board Review

The full shadow export has:

- `211` total rows
- `0` rows for 1.03
- `10` rows for 1.04
- `10` premium shadow rows

Every premium row is marked:

- `promotion_status=shadow_only`
- `production_allowed=no`

The 1.04 rows are ordered for manual review only. Notes on each premium row state that 1.03 remains empty unless source artifacts change, 1.04 remains manual-review only, and no player is automatically promoted.

Jordyn Tyson remains visible in the premium shadow group with injury/manual-review context surfaced. His row carries `manual_flag_count=18`, `remaining_gap_count=7`, prohibited source warnings quarantined as `ranking|rankings`, and notes stating that injury review is surfaced prominently and should not auto-open a premium pick.

## Round 2 Board Review

The Round 2 export contains `9` rows, all in `round2_shadow_review`, and all are RB review profiles inherited from Step 2. The ordering is deterministic from review metadata: review bucket, review status, source confidence, hard-cap presence, remaining gaps, manual flags, position, player name, and player id.

Round 2 rows preserve RB survival questions such as pass protection, contact/survival fields, first-down/short-yardage context, fumbles, special teams, and remaining gaps. No production ranking or final recommendation is created.

No WR/TE/QB Round 2 rows appear in the current Step 2 source artifacts, so no cross-position Round 2 separation is introduced by Step 3.

## 5.04 Watchlist Review

The shadow export contains:

- `119` rows in `5_04_shadow_watchlist`
- `43` rows in `capped_shadow_review`
- `30` rows in `manual_shadow_review`

Hard-capped 5.04 players are prevented from sorting above uncapped watchlist rows because capped rows are assigned `capped_shadow_review` and sort after the review/watchlist groups.

The 5.04 watchlist remains shadow-only and should not be read as a final late-pick ranking. It generally prioritizes uncapped watchlist context over generic capped profiles, but the missing `tag_summary` column limits direct visibility into the asymmetric-role rationale in Step 3 itself. This is a warning for future cleanup, not a blocker.

## Manual-Review Flag Review

Manual flags are preserved through:

- `manual_review_flags`
- `manual_flag_count`
- `remaining_true_gaps`
- `remaining_gap_count`
- `source_conflict_status`
- `notes`

Urgent manual-review context remains visible, including:

- premium WR route/separation/press/YAC questions;
- Jordyn Tyson injury/manual-review concerns;
- RB pass-protection/survival/contact/fumble questions;
- QB and TE exception discounting through capped or manual shadow groups;
- source warnings quarantined in warning fields.

Missing data and remaining gaps reduce confidence through the ordering key rather than creating fake certainty.

## Implementation Safety Review

The shadow builder imports only Python standard-library modules:

- `argparse`
- `csv`
- `sys`
- `collections.Counter`
- `pathlib.Path`
- `typing.Iterable`

The builder does not import Streamlit/app modules, outcome-column modules, or veteran outcome-head modules. It does not read or write `data/`.

The builder writes only local export files under:

`local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`

Generated local exports are not tracked by git and were not committed.

Every exported row has:

- `promotion_status=shadow_only`
- `production_allowed=no`

Validation found `0` rows missing either marker.

## Validation Results

Commands run:

- `git status --short`
- `git diff --check`
- `python scripts/rookie_framework/build_rookie_review_board_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict`
- `python -m pytest tests/test_rookie_shadow_ranking_v03.py -q`
- direct Step 3 test harness

Results:

- `git diff --check`: passed
- review-board strict rebuild: passed
  - `review_rows=211`
  - `premium_rows=10`
  - `round2_rows=9`
  - `watch_rows=119`
- shadow strict rebuild: passed
  - `shadow_rows=211`
  - `premium_rows=10`
  - `round2_rows=9`
  - `watch_rows=119`
- pytest: unavailable in both available Python runtimes
- direct Step 3 test harness: `7/7` passed

## Safety Verification

- `data/` remains untracked and uncommitted.
- `local_exports/` outputs are not committed.
- No rankings, scoring, app, probability, outcome, veteran, private-score, formula, or Streamlit files changed.
- No push was performed.

## Whether Step 5 Is Cleared

Step 5 is cleared only for a rookie-only follow-up. Production promotion is not cleared.

Because this audit is GREEN but has one cleanup warning, the safest Step 5 is a shadow-ranking patch queue, not a user-facing rookie draft packet yet.

## Recommended Step 5

Create a shadow-ranking patch queue for non-blocking cleanup. Suggested first row:

- Carry `tag_summary` or an equivalent `shadow_role_context` field into the shadow export so the 5.04 asymmetric-role rationale is visible directly in Step 3 outputs.

Do not promote production rankings yet.
