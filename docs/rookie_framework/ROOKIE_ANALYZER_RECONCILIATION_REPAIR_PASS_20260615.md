# Rookie Analyzer Reconciliation Repair Pass

Date: 2026-06-15

Lane: Rookie Codex lane only

Verdict: GREEN for safer manual draft advisory use; not approved for production.

## Executive Summary

This repair pass fixed the narrow evidence-to-analyzer bridge issue identified in the reconciliation audit. It carried approved source-safe local context from the existing rookie normalization/source-hit exports into the Step 2 review board for the 10 priority reconciliation players only.

The repair did not create production rankings, private scores, probabilities, bands, app outputs, Streamlit wiring, hidden sort keys, promoted artifacts, outcome columns, or veteran outcome-head usage.

The repaired advisory board is safer than the prior top table because source-safe context and missing-field warnings are now visible for priority players that were previously buried as `unavailable` with little explanation.

## Files Changed

- `scripts/rookie_framework/build_rookie_review_board_v03.py`
- `scripts/rookie_framework/build_rookie_production_candidate_v03.py`
- `tests/test_rookie_review_board_v03.py`
- `tests/test_rookie_production_candidate_v03.py`
- `docs/rookie_framework/ROOKIE_ANALYZER_RECONCILIATION_REPAIR_PASS_20260615.md`

## Local-Only Exports Created

Created under:

`local_exports/rookie_framework/analyzer_reconciliation_repair_pass_20260615/`

Files:

- `rookie_reconciliation_repair_results_20260615.csv`
- `rookie_manual_advisory_board_repaired_20260615.csv`
- `rookie_repaired_warnings_review_20260615.csv`
- `README_ROOKIE_ANALYZER_RECONCILIATION_REPAIR_PASS_20260615.md`

These exports are local-only and must not be committed.

## Repair Method

The review-board builder now applies a priority-player-scoped repair context from existing rookie-only local exports:

- `deep_research_intake_pass_04/applied_framework_after_deep_research_pass04/rookie_framework_v02_tags_after_deep_research_pass04.csv`
- `local_source_search_01/local_source_hit_inventory.csv`

The repair does these things only for the 10 priority reconciliation players:

- preserves source-safe evidence summaries that were already present in local rookie exports;
- fills visible manual-review flags from approved review tags;
- fills visible remaining-gap fields from approved missing-data tags;
- carries source-safe local source-hit context into evidence summaries;
- upgrades source confidence only when the existing local tag-confidence field supports it;
- records Omar Cooper Jr. as an alias for Omar Cooper;
- keeps all repaired rows warning-visible.

The repair does not:

- create clean `ready` rows;
- lower TE replacement gates;
- open hold-until-roster-declaration rows;
- force 1.03 open;
- use ADP, public rankings, projections, consensus, market, trade, or private-score fields as private value.

## Status Counts After Repair

- `ready`: 0
- `rankable_with_warning`: 47
- `manual_review_required`: 7
- `blocked`: 43
- `unavailable`: 114
- analyzer rows: 211

Previous reconciliation state had 42 `rankable_with_warning` rows and 119 `unavailable` rows. Five priority players moved from `unavailable` to warning-rankable manual advisory status.

## Priority Player Results

| Player | Result | Analyzer Status | Notes |
|---|---|---|---|
| Carnell Tate | repaired_rankable_with_warning | rankable_with_warning | Source-safe target-command context and missing-field warnings now visible. |
| Nicholas Singleton | repaired_rankable_with_warning | rankable_with_warning | Existing RB source-safe context and medium tag confidence now flow into analyzer warnings. |
| Barion Brown | repaired_rankable_with_warning | rankable_with_warning | Source-safe target-command context and missing-field warnings now visible. |
| Antonio Williams | repaired_rankable_with_warning | rankable_with_warning | Source-safe target-command context and missing-field warnings now visible. |
| Jadarian Price | repaired_rankable_with_warning | rankable_with_warning | Existing RB touch/goal-line proxy context now flows into analyzer warnings. |
| Kenyon Sadiq | correctly_unavailable | unavailable | TE_REPLACEABLE and low-confidence TE gate remain conservative. |
| Max Klare | correctly_unavailable | unavailable | TE_REPLACEABLE and low-confidence TE gate remain conservative. |
| Jack Velling | correctly_unavailable | unavailable | `hold_until_roster_declaration` remains active. |
| Eli Stowers | correctly_manual_review_required | manual_review_required | TE exception and receiving-vs-blocking usage still require human review. |
| Omar Cooper Jr. | alias_repaired | rankable_with_warning | Alias is documented as Omar Cooper; warning-visible row remains available. |

## Validation Commands Run

```powershell
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

Pytest result: unavailable. The environment returned `No module named pytest`. No package was installed.

Additional CSV sanity check result: PASS.

The sanity check confirmed:

- no duplicate rookie IDs;
- no missing names;
- no missing status labels;
- warnings visible for all repaired rankable rows;
- prohibited source terms are not private input columns;
- no production-ready flags were promoted;
- `app_ready=no`;
- `production_score_created=no`;
- `probabilities_created=no`.

## Manual Draft Use Verdict

The repaired advisory board is safer than the prior top-10 table because important source-safe context now reaches the analyzer for the repaired players.

It remains manual-use only:

- no player is clean `ready`;
- all repaired players remain `rankable_with_warning`, `manual_review_required`, or `unavailable`;
- warnings and remaining gaps must be read before any pick;
- 1.03 remains trade-down/manual-review unless separately approved.

## Remaining Blockers

Tim should not draft from the board confidently without still reviewing:

- repaired WR route/separation/press/YAC and first-down gaps;
- Nicholas Singleton and Jadarian Price RB contact, first-down, fumble, pass-pro, and role questions;
- TE replacement/target-path questions for Kenyon Sadiq, Max Klare, Jack Velling, and Eli Stowers;
- roster declaration context for Jack Velling;
- all visible `draft_only_if` and `do_not_draft_if` fields.

## Production Stop

This pass does not approve production implementation.

Do not use these outputs for:

- production rankings;
- private-score replacement;
- app or Streamlit display;
- probabilities;
- bands;
- outcome columns;
- veteran outcome heads;
- hidden sort keys;
- promoted model artifacts.

## Recommended Next Step

Run a rookie-only draft-room rehearsal using the repaired manual advisory board and Tim's pick sequence. The next task should produce a no-commit checklist that asks the remaining manual questions for 1.03, 1.04, 2.04, 2.08, and 5.04.
