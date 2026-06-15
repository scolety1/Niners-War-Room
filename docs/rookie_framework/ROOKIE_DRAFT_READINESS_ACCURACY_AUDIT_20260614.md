# Rookie Draft-Readiness Accuracy Audit - 2026-06-14

## Verdict For Manual Draft Use

Verdict: `YELLOW_MANUAL_USE_ONLY`.

The isolated rookie analyzer is trustworthy enough for Tim to use manually as a rookie advisory board, provided he treats it as a warning-visible review tool and not as final rankings. It is not safe for production ranking, private-score replacement, app display, probabilities, bands, or veteran outcome-head use.

The analyzer passed strict builds and direct harnesses. It has strong internal row consistency: review board, shadow ranking, production-candidate export, and analyzer export all contain the same `211` rookie IDs with no analyzer duplicate player IDs.

The YELLOW rating is because `ready=0`, seven rows still require manual review, `1.03` remains no-player-cleared, and many profiles remain blocked or unavailable. That is acceptable for manual draft preparation, but not for automatic production use.

## Whether Rookie Rankings Are Usable Manually Today

Yes, but only as a manual advisory board.

Tim can use the analyzer order, pick-fit fields, draft-day simulation, warnings, blockers, and `draft_only_if` / `do_not_draft_if` questions during the draft. He should not use it as a blind ranking list.

Current analyzer counts:

- total analyzer rows: `211`
- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

Current simulation counts:

- total simulation rows: `77`
- `1.03`: `1`
- `1.04`: `9`
- `2.04`: `10`
- `2.08`: `12`
- `5.04`: `45`
- pick cards: `5`

Every analyzer and simulation row remains:

- `app_ready=no`
- `production_score_created=no`
- `probabilities_created=no`

Simulation rows also remain:

- `simulation_only=yes`

## Top Blockers

- `ready=0`; there are no clean production-ready rows.
- `1.03` remains no-player-cleared and should be treated as trade-down/manual-review only.
- Seven rows remain `manual_review_required`.
- `blocked` and `unavailable` rows remain non-actionable.
- No app display contract has been implemented.
- No production ranking/private-score integration has been approved.
- No probabilities or bands exist.
- Pytest is unavailable in the current environment.
- There is no external canonical full-rookie-universe check in this audit, so missing rookies are verified only against the existing internal review/shadow/candidate/analyzer pipeline.

## Top Warning Areas

- Premium WR route, separation, press, YAC, manufactured-touch, target-earning, and first-down evidence remain warning-heavy.
- RB pass protection, contact balance, fumble, receiving first-down, rushing first-down, goal-line role, and injury context remain warning-heavy.
- Jordyn Tyson and Kaelon Black remain premium manual-review cases.
- Round 2 manual-review rows require human answers before draft use.
- TE/QB exceptions remain conservative and should not be forced.
- Late 5.04 profiles are useful as darts only when the role path is visible; many remain source-limited, blocked, or unavailable.
- Return value exists only as limited context. The analyzer is not a complete return-yard scoring optimizer.

## Files Inspected

Tracked docs:

- `docs/rookie_framework/ROOKIE_ANALYZER_FINAL_CHECKPOINT_20260613.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_FINAL_ADVERSARIAL_AUDIT_20260613.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_POST_RECONCILIATION_STATUS_20260614.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_PRODUCTION_APPROVAL_READINESS_PATH_20260614.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_OUTPUT_GUIDE_20260613.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_REVIEW_GUIDE_20260613.md`
- `docs/rookie_framework/ROOKIE_ANALYZER_PICK_FIT_20260613.md`
- `docs/rookie_framework/ROOKIE_DRAFT_DAY_SIMULATION_20260613.md`
- `docs/rookie_framework/ROOKIE_PRODUCTION_CANDIDATE_STATUS_AUDIT_20260613.md`

Tracked scripts:

- `scripts/rookie_framework/build_rookie_review_board_v03.py`
- `scripts/rookie_framework/build_rookie_shadow_ranking_v03.py`
- `scripts/rookie_framework/build_rookie_production_candidate_v03.py`
- `scripts/rookie_framework/build_rookie_analyzer_v03.py`
- `scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py`

Tracked direct harnesses:

- `tests/test_rookie_review_board_v03.py`
- `tests/test_rookie_shadow_ranking_v03.py`
- `tests/test_rookie_production_candidate_v03.py`
- `tests/test_rookie_analyzer_v03.py`
- `tests/test_rookie_draft_day_simulation_v03.py`

Local-only exports:

- `local_exports/model_v4/rookie_framework_v02/review_board_v03/`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`
- `local_exports/model_v4/rookie_framework_v02/production_candidate_v03/`
- `local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/`
- `local_exports/model_v4/rookie_framework_v02/draft_day_simulation_v03/`
- `local_exports/rookie_framework/draft_readiness_accuracy_audit_20260614/`

## Exact Commands Run

```powershell
git rev-parse --show-toplevel; git branch --show-current; git status --short; git log --oneline -10
Get-ChildItem docs/rookie_framework | Select-Object Name,Length | Sort-Object Name
Get-ChildItem scripts/rookie_framework | Select-Object Name,Length | Sort-Object Name
Get-ChildItem tests | Where-Object {$_.Name -like '*rookie*'} | Select-Object Name,Length | Sort-Object Name
git diff --check
python scripts/rookie_framework/build_rookie_review_board_v03.py --strict
python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict
python scripts/rookie_framework/build_rookie_production_candidate_v03.py --strict
python scripts/rookie_framework/build_rookie_analyzer_v03.py --strict
python scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py --strict
python tests/test_rookie_review_board_v03.py
python tests/test_rookie_shadow_ranking_v03.py
python tests/test_rookie_production_candidate_v03.py
python tests/test_rookie_analyzer_v03.py
python tests/test_rookie_draft_day_simulation_v03.py
python -m pytest tests/test_rookie_analyzer_v03.py tests/test_rookie_draft_day_simulation_v03.py -q
```

Additional local CSV inspection and local audit-export generation were run with inline Python. No packages were installed.

## Failed Or Missing Checks

- `pytest` is unavailable: `No module named pytest`.
- No package installation was performed.
- No external full 2026 rookie universe was introduced, so missing-rookie detection is limited to internal consistency across review, shadow, candidate, and analyzer exports.
- No independent current NFL team/staleness service was used; the analyzer contains school/context fields and keeps Roster Declaration Day as a blocker.

## Row Quality Audit

GREEN for internal consistency.

Internal row matching:

- review rows: `211`
- shadow rows: `211`
- production-candidate rows: `211`
- analyzer rows: `211`
- review/analyzer ID mismatch: `0`
- candidate/analyzer ID mismatch: `0`

Duplicate audit:

- review duplicate rookie IDs: `0`
- shadow duplicate rookie IDs: `0`
- production-candidate duplicate rookie IDs: `0`
- analyzer duplicate rookie IDs: `0`

Simulation rows intentionally repeat players across pick contexts, so simulation duplicate player IDs are expected and not a defect.

Missing / placeholder audit:

- missing player names: `0`
- missing positions: `0`
- missing schools: `0`
- missing evidence summaries: `0`
- missing tag summaries: `0`
- missing warnings: `0`
- missing draft-only-if text: `0`
- missing do-not-draft-if text: `0`
- bad positions outside QB/RB/WR/TE: `0`
- placeholder player names: `0`

Warning visibility:

- `rankable_with_warning` rows missing warnings: `0`
- `manual_review_required` rows missing warning/context text: `0`

## Source Contamination Audit

GREEN.

No analyzer/candidate/review CSV column names use prohibited private-input fields such as ADP, rankings, projections, consensus, market, trade value, draft-kit rank, league rank, legacy `private_score`, or fantasy forecast.

Text hits for terms such as ADP, ranking, projection, market, and private_score appear in explicit quarantine/warning or "do not use" context, not as private score inputs. The builders' strict modes continue to reject prohibited private-input columns.

## Scoring-Format Fit Audit

League context:

- 10 teams
- dynasty/keeper hybrid
- 1QB
- non-PPR
- first-down scoring: `0.4` rush/rec first down
- passing yards: `1 per 30`
- passing TD: `3`
- interception: `-1`
- rush/rec yards: `1 per 10`
- rush/rec TD: `4`
- return yards: `1 per 30`
- return TD: `4`
- 2-point conversions: `2`
- fumble lost: `-1`

1QB handling:

- all QB analyzer rows are blocked;
- no QB row is `rankable_with_warning`;
- this is appropriately conservative for a 10-team 1QB league.

Non-PPR RB/WR/TE balance:

- the analyzer does not promote PPR reception volume as a standalone production score;
- RB and WR review context emphasizes role path, first downs, TD/goal-line context, and source-safe evidence;
- TE exceptions remain conservative and manual.

First-down scoring:

- first-down fields are visible in warnings, gaps, and manual review context;
- RB/WR/TE role stability is treated as evidence to review, not as an app-ready score;
- this aligns with the league's first-down scoring emphasis.

Dynasty/keeper context:

- tag summaries and role-path signals help Tim think beyond one-year redraft usage;
- the analyzer does not appear to over-promote pure NFL draft capital as a private score;
- long-term value remains a manual judgment, especially for late 5.04 stashes.

Return scoring:

- special teams / return value appears as limited context where available;
- the analyzer should not be treated as a complete return-yard scoring optimizer.

## Do Not Use For Production Yet

Do not use this analyzer for production yet.

Specifically, do not:

- wire it into Streamlit/app pages;
- replace production rankings;
- overwrite private scores;
- create rookie probabilities;
- create probability bands;
- create app-readable probability or band columns;
- use veteran outcome heads;
- force rookies through veteran outcome heads;
- promote analyzer order into official rankings;
- hide warnings to make rows appear clean;
- use ADP, rankings, projections, market, trade, consensus, or draft-kit sources as private-value inputs.

## How Tim Can Safely Use This In Draft

Tim can safely use the analyzer manually as follows:

1. Treat `1.03` as no-player-cleared unless Tim/HQ manually opens it.
2. Use `1.04` rows only with warnings visible.
3. Read `draft_only_if` and `do_not_draft_if` before selecting any player.
4. Treat `manual_review_required` as a stop sign until Tim answers the manual question.
5. Treat `blocked` and `unavailable` as non-actionable.
6. Use Round 2 rows as RB/WR evidence checks, not automatic picks.
7. Use 5.04 rows as dart/stash context, not safe rankings.
8. Prefer visible role path, first-down stability, TD path, injury clarity, and source-safe evidence over generic upside language.

## Local-Only Audit Exports Created

Created under:

`local_exports/rookie_framework/draft_readiness_accuracy_audit_20260614/`

Files:

- `rookie_manual_advisory_board_20260614.csv`
- `rookie_manual_warnings_review_20260614.csv`
- `rookie_draft_readiness_summary_20260614.csv`
- `README_ROOKIE_DRAFT_READINESS_ACCURACY_AUDIT_20260614.md`

These are local-only and must not be committed.

## Next Best Prompt Recommendation

Next best prompt:

Run a rookie-only manual draft-use rehearsal against Tim's actual pick sequence and league scoring, using the local analyzer exports only. Produce a no-commit draft-room checklist that asks Tim the remaining manual questions for `1.03`, `1.04`, `2.04`, `2.08`, and `5.04`.

Do not start production/app integration from this audit.
