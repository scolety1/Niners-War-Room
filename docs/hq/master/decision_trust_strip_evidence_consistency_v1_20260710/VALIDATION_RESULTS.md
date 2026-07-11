# Validation Results

## Starting state

- Live HQ: `3f41919c506175293465b134f1495c042f710168` — PASS, no remote advance.
- Worktree/branch isolation: PASS.
- Mandatory field reuse and semantic preflight: PASS; no source or identity conflict.

## Focused and regression tests

Command:

`python -m pytest tests/test_decision_trust_strip_service.py tests/test_decision_trust_strip_surfaces.py tests/test_decision_trust_strip_render.py tests/test_dynasty_rankings_page.py tests/test_dynasty_rankings_page_v1.py tests/test_player_compare_decision_service.py tests/test_player_compare_display_only_ngs.py tests/test_player_compare_nflverse_context.py tests/test_player_compare_safe_context_upgrade.py tests/test_trading_lab_manual_planner_safe_upgrade.py tests/test_trading_lab_nflverse_context_service.py tests/test_player_detail_card_component.py tests/test_player_detail_card_service.py tests/test_player_detail_panel.py tests/test_navigation_compression.py -q`

Result: PASS — 125 passed in 1.83 seconds.

This includes schema/state contract tests, all three surface source checks, representative Streamlit AppTest rendering, affected surface regressions, existing receipt/detail components, and navigation/route smoke coverage.

The pre-existing `tests/test_trust_banner_ui.py` result is 3 passed / 2 failed on both this lane and a clean live-HQ worktree. Both failures concern the unchanged thin wrapper `app/pages/05_rankings.py`; no test was weakened and no out-of-scope repair was made.

## Compilation and static analysis

- In-memory Python compilation: PASS — five affected implementation/page files.
- `python -m ruff check` on all affected implementation, page, test, and fixture files: PASS.

## Render and accessibility

- Streamlit AppTest representative fixture: PASS — seven compact summaries and seven expandable disclosures, no exceptions.
- Text state labels and icon-plus-text semantics: PASS.
- Existing keyboard-operable `st.expander` disclosure: PASS.
- No custom CSS, fixed layout, focus trap, or color-only state: PASS.

## Documentation and CSV validation

- Required documentation files: PASS — all 15 required, non-empty.
- Bundled `@oai/artifact-tool` CSV import/inspection: PASS — five CSV ledgers.
- CSV duplicate-key checks: PASS.
- Field reuse rows: 6; state glossary rows: 8; surfaces: 3; fixture states: 8; changed paths: 24.
- Schema/glossary/order consistency: PASS.

## Safety and repository gates

- Scores/ranks/formulas/rank assignment: unchanged.
- Default sorting, recommendations, eligibility and filters: unchanged.
- Trading valuation/draft valuation: unchanged; Trading Lab remains manual.
- Source registries, admission and refresh behavior: unchanged.
- Frozen 2026 packet and operational closeout: unchanged.
- No PYF, GAUNTLET_081, current-board freeze, or outcome artifact dependency in app logic.
- Allowed-scope/protected-path scan: PASS.
- `git diff --check`: PASS.
- `git diff --cached --check`: rerun after staging.
- Push: NOT AUTHORIZED / NOT PERFORMED.

Clean-worktree verification is completed after the local commit.
