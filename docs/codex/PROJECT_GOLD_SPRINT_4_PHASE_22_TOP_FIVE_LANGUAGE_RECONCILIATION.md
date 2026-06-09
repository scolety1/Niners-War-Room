# Project Gold Sprint 4 / Phase 22: Top-Five Rule Language Reconciliation

Last reviewed: 2026-05-14

This phase is a language-only pass. It does not change formulas, scoring,
rankings, readiness gates, league-rank imports, or forced-release selection.

## Decision

Use these user-facing terms:

| concept | user-facing term | meaning |
|---|---|---|
| roster-scoped top five | Roster's League-Rank Top Five | The five highest league-ranked players on that roster. |
| forced top-five release | Required Top-Five Release Slot | The roster top-five player who currently satisfies the declaration rule. |
| rule column | Top-Five Rule Status | Whether a player is required, protected, or outside the roster top-five rule group. |

## Clarification

Roster's League-Rank Top Five does **not** mean league ranks 1-5 overall. It
means the five best league-rank numbers on a single roster. League rank is a
rule and availability signal only. It is not player quality and should not enter
private/model value.

## Files Updated

- `src/services/command_board_service.py`
- `src/services/forced_release_strategy_service.py`
- `src/services/league_service.py`
- `src/services/app_workflow_service.py`
- `src/services/data_pack_admission_service.py`
- `src/services/data_pack_health_service.py`
- `src/services/ranking_surface_audit_service.py`
- `src/services/ranking_surface_service.py`
- `src/services/my_team_decision_receipts_service.py`
- `app/pages/02_team.py`
- `app/pages/03_war_board.py`
- `app/pages/06_league_intel.py`
- `README.md`
- `docs/codex/DATA_CONTRACT.md`
- affected tests

## Expected Result

The app should no longer imply that a top-five row must have league rank 1-5
overall. It should show that the rule is roster-scoped and that league rank is
only the declaration-rule signal.
