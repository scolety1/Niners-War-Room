# Pro Agent Audit Prompt

You are auditing the Niners War Room Model v4 repair run.

Repo:
`C:\Dev\niners-war-room`

Current project mode:
Paused / inspect-and-repair only.

Your job is to determine whether the source-routing, score-disclosure, market-isolation,
copy, rookie-label, and sentinel regression repairs are safe enough to preserve before
any future formula tuning. Do not tune formulas.

## Read First

1. `docs/model_v4/5-30_NEW_CHAT_HANDOFF.md`
2. `docs/model_v4/REPAIR_TASK_QUEUE_20260530.md`
3. `docs/model_v4/MODEL_V4_REPAIR_EXTERNAL_AUDIT_PACKAGE_20260530.md`
4. `docs/model_v4/MODEL_V4_REPAIR_ACCEPTANCE_CHECKLIST_20260530.md`

## Inspect These Core Files

1. `src/services/review_score_envelope_service.py`
2. `src/services/player_board_score_service.py`
3. `src/services/market_gap_service.py`
4. `src/services/model_v4_startup_slot_simulator_service.py`
5. `src/services/model_v4_roster_opportunity_cost_service.py`
6. `src/services/model_v4_rookie_pick_decision_lab_service.py`
7. `src/services/model_v4_sprint14c_trade_review_service.py`
8. `app/pages/04_trade_central.py`
9. `app/pages/05_rankings.py`
10. `app/pages/06_draft_board.py`
11. `app/pages/08_june15_review.py`
12. `app/components/trust_status.py`

## Inspect These Tests

1. `tests/test_model_v4_final_sentinel_gate.py`
2. `tests/test_review_score_envelope_service.py`
3. `tests/test_player_board_score_service.py`
4. `tests/test_market_gap_service.py`
5. `tests/test_model_v4_rookie_pick_decision_lab_service.py`
6. `tests/test_model_v4_startup_slot_simulator_service.py`
7. `tests/test_model_v4_roster_opportunity_cost_service.py`
8. `tests/test_model_v4_sprint14c_trade_review_service.py`
9. `tests/test_trust_banner_ui.py`
10. `tests/test_model_v4_phase5_clean_display_language.py`
11. `tests/test_navigation_compression.py`

## Hard Guardrails

- Do not tune formulas, model weights, veteran age curves, rookie weights, pick baselines, VORP, replacement formulas, market-gap thresholds, confidence cap magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, or trade-calculator logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell, defer, or target recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app promotion, or active app state.

## Required Verification Points

1. Player Board primary value uses:
   - `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
   - column `checkpoint_review_score`

2. Legacy active-pack `private_score` is comparison-only:
   - Keenan Allen legacy `82.4` must not be primary.
   - Darius Slayton legacy `78.88` must not be primary.

3. Missing, duplicate, stale, or partially quarantined joins fail closed into manual review.

4. Market context is display-only:
   - no primary review score,
   - no primary review label,
   - no private-value routing,
   - no action-like application hints.

5. Cross-asset exports disclose:
   - `source_path`,
   - `source_column`,
   - `lineage_class`.

6. Rookie Pick Decision Lab neutral labels are limited to:
   - `use_pick_review`,
   - `hold_pick_value_context`,
   - `manual_decision_required`.

7. Future-pick/current-player comparison modes require concrete comparator rows.

8. UI pages show review-only banner and score disclosure without recommendations.

## Suggested Commands

Run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_model_v4_final_sentinel_gate.py tests\test_review_score_envelope_service.py tests\test_player_board_score_service.py tests\test_market_gap_service.py tests\test_model_v4_rookie_pick_decision_lab_service.py tests\test_model_v4_startup_slot_simulator_service.py tests\test_model_v4_roster_opportunity_cost_service.py tests\test_model_v4_sprint14c_trade_review_service.py tests\test_trust_banner_ui.py tests\test_model_v4_phase5_clean_display_language.py tests\test_navigation_compression.py -q
```

Also run:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check tests\test_model_v4_final_sentinel_gate.py tests\test_review_score_envelope_service.py tests\test_player_board_score_service.py tests\test_market_gap_service.py tests\test_model_v4_rookie_pick_decision_lab_service.py tests\test_model_v4_startup_slot_simulator_service.py tests\test_model_v4_roster_opportunity_cost_service.py tests\test_model_v4_sprint14c_trade_review_service.py tests\test_trust_banner_ui.py tests\test_model_v4_phase5_clean_display_language.py tests\test_navigation_compression.py
```

## Return Format

Return:

- Verdict: `repair_gate_passed_for_review_only_source_routing` or `needs_repair_before_formula_tuning`
- Critical blockers
- High-priority issues
- Medium/low issues
- Sentinel result summary for Keenan Allen and Darius Slayton
- Market leakage verdict
- Rookie label/comparison gate verdict
- UI copy and disclosure verdict
- Cross-asset source disclosure verdict
- Test commands run and results
- Residual risks
- Next recommended action

Ground every issue in file and line references.
