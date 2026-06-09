# Model v4 Repair External Audit Package

Date: 2026-05-30

Mode: paused / inspect-and-repair only.

This package is for an external ChatGPT Pro audit of the Niners War Room Model v4
source-routing and review-safety repair run. It is not a formula tuning packet.

## Audit Goal

Verify that the app now protects review-only Model v4 values from:

- legacy active-pack `private_score` leakage,
- market, ADP, ranking, projection, mock, consensus, or trade-calculator leakage,
- silent source/lineage ambiguity,
- recommendation-like trade, cut, keep, draft, buy, sell, target, or defer labels,
- rookie pick comparison labels without concrete comparator rows.

## Primary Context Files

- `docs/model_v4/5-30_NEW_CHAT_HANDOFF.md`
- `docs/model_v4/REPAIR_TASK_QUEUE_20260530.md`
- `docs/model_v4/MODEL_V4_REPAIR_PRO_AGENT_PROMPT_20260530.md`
- `docs/model_v4/MODEL_V4_REPAIR_ACCEPTANCE_CHECKLIST_20260530.md`

## Key Code Files To Inspect

- `src/services/review_score_envelope_service.py`
- `src/services/player_board_score_service.py`
- `src/services/market_gap_service.py`
- `src/services/model_v4_startup_slot_simulator_service.py`
- `src/services/model_v4_roster_opportunity_cost_service.py`
- `src/services/model_v4_rookie_pick_decision_lab_service.py`
- `src/services/model_v4_sprint14c_trade_review_service.py`
- `src/services/model_v4_identity_join_gate_service.py`
- `src/services/model_v4_evidence_gate_service.py`
- `app/pages/04_trade_central.py`
- `app/pages/05_rankings.py`
- `app/pages/06_draft_board.py`
- `app/pages/08_june15_review.py`
- `app/components/trust_status.py`

## Key Test Files To Inspect

- `tests/test_model_v4_final_sentinel_gate.py`
- `tests/test_review_score_envelope_service.py`
- `tests/test_player_board_score_service.py`
- `tests/test_market_gap_service.py`
- `tests/test_model_v4_rookie_pick_decision_lab_service.py`
- `tests/test_model_v4_startup_slot_simulator_service.py`
- `tests/test_model_v4_roster_opportunity_cost_service.py`
- `tests/test_model_v4_sprint14c_trade_review_service.py`
- `tests/test_trust_banner_ui.py`
- `tests/test_model_v4_phase5_clean_display_language.py`
- `tests/test_navigation_compression.py`

## Changed Surface Summary

1. Shared score envelope and source routing:
   - Added/used a shared `ReviewScoreEnvelope`.
   - Required source path, score column, model version, lineage, score type, confidence cap, warning flags, allowed use, and blocked use.
   - Unknown, legacy, and market-only lineages fail closed as primary score sources.

2. Player Board source routing:
   - Primary Player Board value now routes to
     `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
     column `checkpoint_review_score`.
   - Legacy active-pack `private_score` is comparison-only as `legacy_active_pack_score`.
   - Keenan Allen legacy `82.4` is not primary.
   - Darius Slayton legacy `78.88` is not primary and fails closed when no Model v4 row exists.

3. Join and evidence gates:
   - Duplicate or unmatched identity joins require manual review.
   - Stale team/status, missing role evidence, and partial/quarantined contributions require manual review.

4. Market no-leakage:
   - Market rows are display-only and expose `market_display_only`.
   - Market rows do not populate primary review score or review label.
   - Action-like market hint terms were removed.

5. External Asset Reviews and neutral copy:
   - Trade Review language was reframed as External Asset Reviews.
   - Buy/sell/target/trade-for framing was quarantined from repaired review surfaces.
   - Review-only banner text was added:
     `Review-only surface. This page does not make automatic trade, cut, keep, or draft recommendations.`

6. Cross-asset export disclosure:
   - Startup Slot, Roster Opportunity Cost, Rookie Pick Decision Lab, and External Asset Review exports disclose `source_path`, `source_column`, and `lineage_class`.

7. Rookie pick gates:
   - Neutral board labels are limited to `use_pick_review`, `hold_pick_value_context`, and `manual_decision_required`.
   - Future-pick/current-player comparison modes require concrete comparator rows.
   - Absent trade-down comparators do not emit trade-down comparison mode.

8. UI score disclosure:
   - Player Board and Draft Room surfaces show score source file, score column, score type, model version or formula version, lineage, trust cap, and warnings where available.

## Focused Test Evidence

Last selected repair suite run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_model_v4_final_sentinel_gate.py tests\test_review_score_envelope_service.py tests\test_player_board_score_service.py tests\test_market_gap_service.py tests\test_model_v4_rookie_pick_decision_lab_service.py tests\test_model_v4_startup_slot_simulator_service.py tests\test_model_v4_roster_opportunity_cost_service.py tests\test_model_v4_sprint14c_trade_review_service.py tests\test_trust_banner_ui.py tests\test_model_v4_phase5_clean_display_language.py tests\test_navigation_compression.py -q
```

Observed result: `77 passed`.

Focused lint run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check tests\test_model_v4_final_sentinel_gate.py tests\test_review_score_envelope_service.py tests\test_player_board_score_service.py tests\test_market_gap_service.py tests\test_model_v4_rookie_pick_decision_lab_service.py tests\test_model_v4_startup_slot_simulator_service.py tests\test_model_v4_roster_opportunity_cost_service.py tests\test_model_v4_sprint14c_trade_review_service.py tests\test_trust_banner_ui.py tests\test_model_v4_phase5_clean_display_language.py tests\test_navigation_compression.py
```

Observed result: `All checks passed!`

## Residual Risks For Auditor

- Full repository test suite was not run during the final sentinel task.
- The worktree is heavily dirty and many files are untracked in git status.
- This repair package deliberately did not tune formulas or judge football accuracy.
- Legacy services may still contain compatibility fields, but repaired lanes must keep those legacy values comparison-only.
- External audit should verify behavior by reading files and tests, not by assuming package text is sufficient.

## Requested External Verdict

Return one of:

- `repair_gate_passed_for_review_only_source_routing`
- `needs_repair_before_formula_tuning`

Also list blockers, high-priority issues, medium/low issues, and exact file/test references.
