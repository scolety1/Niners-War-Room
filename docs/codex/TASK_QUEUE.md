# Codex Task Queue

## Mission

Build Niners Dynasty: War Room V1, a local-first Drop Deadline Command Center.

## Guardrails

Codex should implement one selected task at a time. PowerShell owns task selection, checks, reviews, reports, and commits.

Codex may:
- edit app, src, tests, docs, scripts, and sample_data files within task scope
- add deterministic formulas and tests
- add local CSV sample fixtures
- improve Streamlit pages after import/model foundations exist

Codex may not:
- require live APIs at runtime
- scrape websites
- add secrets, auth, payments, backend services, deploy config, or production integrations
- edit package/dependency files unless explicitly approved
- edit generated SQLite databases or frozen data_packs
- overwrite old data packs
- build complex ML in V1

## Tasks

- [ ] PERSONAL LOW PRIORITY parking polish: keep Niners War Room parked as a personal project and only make a small table-first polish pass if it is selected later; preserve the current local-first Streamlit/SQLite architecture, no live APIs at runtime, no scraping, no package/dependency edits, no generated database/data_pack changes, no auth/backend/payment/deploy work, and no complex ML. [class:design risk:low mode:single scope:app/,src/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- [x] Task 2 and 3 - CSV import foundation: implement CSV schema validation and local data pack loading for dim_players, fact_rosters, fact_official_rankings, fact_future_picks, fact_pick_values, model_outputs, and metadata_sources; catch duplicate players on multiple teams, duplicate draft picks, missing official rank warnings, rank 400 warnings, invalid pick labels, missing player identity errors, unknown team warnings, and roster count warnings; create sample_data/2026_pre_declaration with small Niners top-five sample files; write to SQLite and record import_errors. [class:feature risk:medium mode:single scope:src/,tests/,scripts/,sample_data/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- [x] Task 4 - Pick value engine: implement the 1,000-point pick value curve, overall pick calculation, future discount, certainty adjustment, declaration adjustment placeholder, trade-up/trade-down helpers, and do-not-draft-before helper with tests for 1.01, 1.04, 2.04, 5.04, and 2027 known-pick discounts. [class:feature risk:medium mode:single scope:src/models/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- [x] Task 5 and 6 - Player and keeper engines: implement QB/RB/WR/TE private score formulas, first-down adjustment helpers, confidence score, official top-five calculation, keeper score, drop candidate score, keeper pressure, best 23 keepers, forced release candidates, and top-five shield eligibility; verify the Niners sample identifies Achane, Lamar, Chase Brown, Luther Burden, and Brian Thomas as official top five. [class:feature risk:medium mode:single scope:src/models/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- [x] Task 8, 9, 10, and 11 - Streamlit command boards: build Import Review, Team, and War Board pages using the active data pack; keep UI table-first and low-text; show validation errors/warnings, Niners official top five, forced-release pressure, keeper/drop/shop recommendations, sortable/filterable War Board, and hidden long explanations. [class:feature risk:medium mode:single scope:app/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- [ ] Task 7, 12, 13, and 14 - Trade, league, and draft rooms: implement trade score formulas, Trade Central V1, League Intel, and Draft Room V1; show shop/drop/shield candidates, keeper pressure by team, and pick value tables. [class:feature risk:medium mode:single scope:app/,src/models/,src/services/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
