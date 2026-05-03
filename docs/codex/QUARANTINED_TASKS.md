# Quarantined Fleet Tasks


## 2026-04-26 03:02:27

- Batch: 1
- Task index: 1
- Task: PERSONAL LOW PRIORITY parking polish: keep Niners War Room parked as a personal project and only make a small table-first polish pass if it is selected later; preserve the current local-first Streamlit/SQLite architecture, no live APIs at runtime, no scraping, no package/dependency edits, no generated database/data_pack changes, no auth/backend/payment/deploy work, and no complex ML. [class:design risk:low mode:single scope:app/,src/,tests/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
- Reason: External build failed after implementation.
- Files restored before continuing:
- app/components/tables.py
- app/pages/01_import_review.py
- app/pages/02_team.py
- app/pages/03_war_board.py
- Next step: Nami should avoid repeating this exact task until a human reviews the failure.

## 2026-05-02 23:59:55

- Batch: 1
- Task index: 1
- Task: VISUAL EVIDENCE RECOVERY - repair the Streamlit visual QA path that produced "Not found" screenshots: add or update local route evidence/config/docs so root, Import Review, Team, War Board, Trade Central, Draft Room, League Intel, and Model Audit can be verified as real Streamlit content on desktop and mobile; add a guard or documented check that fails when captured content contains "Not found" or mostly blank white space. Keep this task evidence-focused and table-first: no broad UI redesign, no new product pages, no live APIs, no scraping, no dependency/package edits, no generated database/data_pack output, no auth/backend/payment/deploy work, and no complex ML. Acceptance: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1, plus updated docs/codex/SIMON_DESIGN_REVIEW.md or visual evidence notes that explain whether the RED can move to YELLOW. [class:bugfix risk:medium mode:single impact:visible scope:app/,scripts/,docs/codex/]
- Reason: Large Phase 3 task requires a concrete slice plan before implementation.
- Files restored before continuing:
- None
- Next step: Nami should avoid repeating this exact task until a human reviews the failure.

## 2026-05-03 02:23:41

- Batch: 1
- Task index: 1
- Task: User pain: the previous task was quarantined before implementation because Large Phase 3 task requires a concrete slice plan before implementation., so the ship needs one small visible repair instead of another broad pass. Target: app/. Change: make exactly one narrow safe slice that improves a visible UI, interaction, or copy area; prefer deleting awkward complexity over adding new systems. First screen: keep the current primary screen job dominant and move any repaired detail/helper content behind the existing clear action. Remove/simplify: one repeated label, one oversized chrome area, one vague phrase, or one confusing interaction in the current surface only. Guardrails: no backend, no auth, no payments, no Firebase rules/config, no package/dependency files, no generated output, no deployment config, no secrets, and no unrelated files. Acceptance: external build or configured acceptance. Check: run the acceptance command and confirm the changed screen has one clearer visible outcome without expanding scope. [class:bugfix risk:low mode:single impact:visible surface:mixed scope:app,scripts,docs/codex]
- Reason: Task-specific acceptance check failed.
- Files restored before continuing:
- app/pages/07_model_audit.py
- Next step: Nami should avoid repeating this exact task until a human reviews the failure.

## 2026-05-03 02:27:41

- Batch: 1
- Task index: 1
- Task: User pain: the previous task was quarantined before implementation because Task-specific acceptance check failed., so the ship needs one small visible repair instead of another broad pass. Target: app/. Change: make exactly one narrow safe slice that improves a visible UI, interaction, or copy area; prefer deleting awkward complexity over adding new systems. First screen: keep the current primary screen job dominant and move any repaired detail/helper content behind the existing clear action. Remove/simplify: one repeated label, one oversized chrome area, one vague phrase, or one confusing interaction in the current surface only. Guardrails: no backend, no auth, no payments, no Firebase rules/config, no package/dependency files, no generated output, no deployment config, no secrets, and no unrelated files. Acceptance: external build or configured acceptance. Check: run the acceptance command and confirm the changed screen has one clearer visible outcome without expanding scope. [class:bugfix risk:low mode:single impact:visible surface:mixed scope:app,scripts,docs/codex]
- Reason: Task-specific acceptance check failed.
- Files restored before continuing:
- app/pages/02_team.py
- Next step: Nami should avoid repeating this exact task until a human reviews the failure.
