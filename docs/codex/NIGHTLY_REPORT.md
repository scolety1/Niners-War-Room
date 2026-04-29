# Codex Nightly Report

## 2026-04-26 00:07:06

- Task attempted: Task 2 and 3 - CSV import foundation: implement CSV schema validation and local data pack loading for dim_players, fact_rosters, fact_official_rankings, fact_future_picks, fact_pick_values, model_outputs, and metadata_sources; catch duplicate players on multiple teams, duplicate draft picks, missing official rank warnings, rank 400 warnings, invalid pick labels, missing player identity errors, unknown team warnings, and roster count warnings; create sample_data/2026_pre_declaration with small Niners top-five sample files; write to SQLite and record import_errors. [class:feature risk:medium mode:single scope:src/,tests/,scripts/,sample_data/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Allowed scope: src, tests, scripts, sample_data, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- sample_data/2026_pre_declaration/dim_players.csv
- sample_data/2026_pre_declaration/fact_future_picks.csv
- sample_data/2026_pre_declaration/fact_official_rankings.csv
- sample_data/2026_pre_declaration/fact_pick_values.csv
- sample_data/2026_pre_declaration/fact_rosters.csv
- sample_data/2026_pre_declaration/metadata_sources.csv
- sample_data/2026_pre_declaration/model_outputs.csv
- scripts/load_data_pack.py
- src/data/csv_schemas.py
- src/data/loaders.py
- src/data/validators.py
- tests/test_import_validation.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-26 00:30:47

- Task attempted: Task 4 - Pick value engine: implement the 1,000-point pick value curve, overall pick calculation, future discount, certainty adjustment, declaration adjustment placeholder, trade-up/trade-down helpers, and do-not-draft-before helper with tests for 1.01, 1.04, 2.04, 5.04, and 2027 known-pick discounts. [class:feature risk:medium mode:single scope:src/models/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Allowed scope: src/models, tests, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- src/models/pick_values.py
- tests/test_pick_values.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-26 00:48:50

- Task attempted: Task 5 and 6 - Player and keeper engines: implement QB/RB/WR/TE private score formulas, first-down adjustment helpers, confidence score, official top-five calculation, keeper score, drop candidate score, keeper pressure, best 23 keepers, forced release candidates, and top-five shield eligibility; verify the Niners sample identifies Achane, Lamar, Chase Brown, Luther Burden, and Brian Thomas as official top five. [class:feature risk:medium mode:single scope:src/models/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Allowed scope: src/models, src/services, tests, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- src/models/confidence.py
- src/models/keeper_scores.py
- src/models/player_scores.py
- src/services/roster_service.py
- src/services/team_service.py
- tests/test_keeper_scores.py
- tests/test_roster_rules.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-26 01:09:56

- Task attempted: Task 8, 9, 10, and 11 - Streamlit command boards: build Import Review, Team, and War Board pages using the active data pack; keep UI table-first and low-text; show validation errors/warnings, Niners official top five, forced-release pressure, keeper/drop/shop recommendations, sortable/filterable War Board, and hidden long explanations. [class:feature risk:medium mode:single scope:app/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Allowed scope: app, src/services, tests, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- app/main.py
- app/pages/01_import_review.py
- app/pages/02_team.py
- app/pages/03_war_board.py
- src/services/command_board_service.py
- tests/test_command_board_service.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-26 03:02:27

- Task attempted: PERSONAL LOW PRIORITY parking polish: keep Niners War Room parked as a personal project and only make a small table-first polish pass if it is selected later; preserve the current local-first Streamlit/SQLite architecture, no live APIs at runtime, no scraping, no package/dependency edits, no generated database/data_pack changes, no auth/backend/payment/deploy work, and no complex ML. [class:design risk:low mode:single scope:app/,src/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]

- Build result: Quarantined
- Files changed:
- app/components/tables.py
- app/pages/01_import_review.py
- app/pages/02_team.py
- app/pages/03_war_board.py
- Risks or follow-up needed: External build failed after implementation.

## 2026-04-27 23:53:15

- Task attempted: CAPTAIN NEXT table-first V1 completion pass: finish one useful table-first slice of V1 by improving Trade Central, League Intel, or Draft Room so it shows real sample-pack data with concise labels and no fantasy-blog prose; preserve local-first CSV/SQLite runtime, no live APIs, no scraping, no package/dependency edits, no generated database/data_pack changes, no auth/backend/payment/deploy work, and no complex ML. [class:feature risk:medium mode:single scope:app/,src/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Task impact: showpiece
- Allowed scope: app, src, tests, docs/codex
- Acceptance checks: external build only
- Build result: Failed
- Files changed:
- app/pages/05_draft_room.py
- src/services/draft_service.py
- tests/test_draft_service.py
- Risks or follow-up needed: External build failed.

## 2026-04-28 00:48:07

- Task attempted: CAPTAIN NEXT table-first V1 completion pass: finish one useful table-first slice of V1 by improving Trade Central, League Intel, or Draft Room so it shows real sample-pack data with concise labels and no fantasy-blog prose; preserve local-first CSV/SQLite runtime, no live APIs, no scraping, no package/dependency edits, no generated database/data_pack changes, no auth/backend/payment/deploy work, and no complex ML. [class:feature risk:medium mode:single scope:app/,src/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Task impact: showpiece
- Allowed scope: app, src, tests, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- app/pages/04_trade_central.py
- src/models/trade_scores.py
- src/services/trade_service.py
- tests/test_trade_scores.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-28 00:56:29

- Task attempted: Task 7, 12, 13, and 14 - Trade, league, and draft rooms: implement trade score formulas, Trade Central V1, League Intel, and Draft Room V1; show shop/drop/shield candidates, keeper pressure by team, and pick value tables. [class:feature risk:medium mode:single scope:app/,src/models/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Task impact: standard
- Allowed scope: app, src/models, src/services, tests, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- app/pages/06_league_intel.py
- src/services/league_service.py
- tests/test_league_service.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-28 23:17:53

- Task attempted: MODEL SPEC ALIGNMENT - pick value curve repair: replace the current placeholder/interpolated pick-value curve with the exact 50-pick 1,000-point curve from the Niners War Room brief, including `1.01=1000`, `1.04=630`, `2.04=200`, `5.04=18`, and `5.10=12`; change the default annual future discount to the brief's 0.80 framework while allowing configurable 0.80-0.82 values; keep overall pick calculation as `10 * (round - 1) + slot`; update `fact_pick_values.csv` sample values only if needed to match deterministic formula outputs; rewrite pick-value tests so they assert the brief values instead of the current placeholder values. Forbidden scope: no live APIs, no scraping, no package/dependency edits, no generated SQLite/data_packs output, no auth/backend/payments/deploy work, no UI redesign, no complex ML, no unrelated model changes. [class:formula risk:medium mode:single impact:standard scope:src/models/,tests/,sample_data/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Task impact: showpiece
- Allowed scope: src/models, tests, sample_data, docs/codex
- Acceptance checks: external build only
- Build result: Passed
- Files changed:
- sample_data/2026_pre_declaration/fact_pick_values.csv
- src/models/pick_values.py
- tests/test_draft_service.py
- tests/test_pick_values.py
- tests/test_trade_scores.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.

## 2026-04-29 10:48:37

- Task attempted: User pain: The Niners owner cannot trust the War Room unless player scores match the written model spec exactly and can be audited. Target: player/private score formulas and tests. Change: replace the current prototype QB/RB/WR/TE private-score formulas with the brief's exact weighted heuristic formulas using normalized 0-100 feature inputs: QB draft_cap/rush_profile/start_path/passing_trait/environment, RB draft_cap/opportunity/production/receiving/elusiveness/size_durability/athleticism, WR draft_cap/age_adj_production/target_earning_efficiency/breakout_class/film_separation/size_role/athleticism/environment, and TE draft_cap/receiving_production/route_role/athleticism/film_receiving/role_path/age_timeline/environment; keep first-down adjustments modest and testable; rewrite tests with hand-calculated fixture values from the brief weights. Remove/simplify: remove placeholder scoring shortcuts and any unsupported hardcoded values outside fixtures/tests. Guardrails: no live APIs, no scraping, no package/dependency edits, no generated SQLite/data_packs output, no auth/backend/payments/deploy work, no UI redesign, no complex ML, no player-data hardcoding outside fixtures/tests. Acceptance: formula tests use hand-calculated fixture values from the brief weights and score outputs are deterministic. Check: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1 [class:formula risk:medium mode:single impact:standard scope:src/models/,tests/,docs/codex/ accept:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Task class: feature
- Task risk: medium
- Task mode: single
- Task impact: showpiece
- Allowed scope: src/models, tests, docs/codex
- Acceptance checks: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1
- Build result: Passed
- Files changed:
- docs/codex/FORMULA_SPEC.md
- src/models/player_scores.py
- tests/test_keeper_scores.py
- Risks or follow-up needed: Low. External build, task acceptance checks, and checkpoint loop review completed.
