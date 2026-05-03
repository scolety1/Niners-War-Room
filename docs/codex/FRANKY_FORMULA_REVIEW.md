# Franky Formula Review

Generated: 2026-05-03 02:28:03
Project: NinersWarRoom
Branch: codex/niners-war-room-NinersWarRoom-20260425-235452
HEAD: f77b540
Base branch: main

## Verdict
RED

## Franky's Read
Franky checked the formula specs, fixture expectations, tests, provenance, and confidence boundaries so analytical work does not become fake-confidence soup.

## Formula Surface
- Formula intent detected: True
- Formula-sensitive changed files: docs/codex/FIXTURE_TEST_PLAN.md, docs/codex/FORMULA_SPEC.md, src/models/confidence.py, src/models/keeper_scores.py, src/models/pick_values.py, src/models/player_scores.py, src/models/trade_scores.py, src/services/command_board_service.py, src/services/draft_service.py, src/services/league_service.py, src/services/roster_service.py, src/services/team_service.py, src/services/trade_service.py, tests/test_import_validation.py, tests/test_keeper_scores.py, tests/test_pick_values.py, tests/test_trade_scores.py
- Analytical phase/docs detected: True
- Test files changed: tests/test_command_board_service.py, tests/test_draft_service.py, tests/test_import_validation.py, tests/test_keeper_scores.py, tests/test_league_service.py, tests/test_pick_values.py, tests/test_roster_rules.py, tests/test_trade_scores.py
- Tracked formula tests: tests/test_import_validation.py, tests/test_keeper_scores.py, tests/test_pick_values.py, tests/test_trade_scores.py
- Dirty files: clean

## Findings
- [RED] FORMULA_SPEC.md needs concrete non-placeholder content under 'Inputs'.
- [RED] FORMULA_SPEC.md needs concrete non-placeholder content under 'Outputs'.

## Required Actions
- Replace the 'Inputs' placeholder with specific formula evidence, not TBD/unknown/later language.
- Replace the 'Outputs' placeholder with specific formula evidence, not TBD/unknown/later language.

## Formula Evidence Rules
- Every formula change needs a plain-English or pseudocode formula in FORMULA_SPEC.md.
- Every important formula needs at least one fixture input and hand-calculated expected output.
- Formula/model code changes need formula-oriented tests or explicit evidence that existing tests cover the behavior.
- User-facing scores, ranks, probabilities, and recommendations must be computed, sourced, or fixture-backed.
- Calibration gaps must be visible; do not let the UI imply certainty the model has not earned.

## Repair Task Draft
- [ ] User pain: Analytical output is blocked by missing formula evidence. Target: docs/codex formula evidence and related tests. Change: resolve Franky's RED findings by adding concrete formulas, fixture rows, expected outputs, and formula test evidence. Remove/simplify: remove placeholder/TBD formula language and unsupported numeric claims. Guardrails: no UI polish, no unrelated feature work, no source-data invention. Acceptance: powershell -NoProfile -ExecutionPolicy Bypass -File ..\codex-fleet\franky-formula-review.ps1 -Repo . [class:test risk:medium mode:single scope:docs/codex/,tests/,src/]

## Stop Or Continue
stop for human formula review
