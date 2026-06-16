# Sprint 5DH: Static App Surface Inventory And Schema-Risk Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_NON_NUMERIC_QA_CONTRACT`

Sprint type: `READ_ONLY_STATIC_INVENTORY_NO_APP_EDIT`

## 1. Scope

Sprint 5DH performs a read-only static inventory of app/source surfaces that a future Outcome Column app-wiring sprint might touch. This sprint is not app wiring. It did not edit app/source files, create app-readable outputs, create current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, change rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, stage or commit `data/`, stage or commit `local_exports/`, push, deploy, use internet lookup, or install packages.

## 2. Read-Only Inventory Commands

Read-only inspection included:

- `rg --files app`
- `rg --files tests`
- targeted reads of `app/navigation.py`
- targeted reads of `app/pages/05_rankings.py`
- targeted reads of `src/services/nwr_outcome_status_display_service.py`
- targeted reads of `tests/test_nwr_outcome_status_display_service.py`
- targeted reads of `tests/test_outcome_column_integration_contract.py`
- targeted reads of `src/services/table_sort_service.py`
- grep-style searches for Outcome/status/rank/sort references

No app/source file was edited.

## 3. Relevant App Surfaces

Visible navigation surfaces:

- `app/main.py`
- `app/navigation.py`
- `app/pages/05_rankings.py`
- `app/pages/08_june15_review.py`
- `app/pages/06_draft_board.py`
- `app/pages/07_live_draft_room.py`
- `app/pages/04_trade_central.py`
- `app/pages/07_source_overrides.py`

Hidden or advanced surfaces that may matter for audits:

- `app/pages/00_command_center.py`
- `app/pages/03_war_board.py`
- `app/pages/02_team.py`
- `app/pages/06_league_intel.py`
- `app/pages/07_model_lab.py`
- `app/pages/09_model_tuning.py`
- `app/pages/10_historical_replay.py`

Relevant components:

- `app/components/player_detail_card.py`
- `app/components/player_detail_panel.py`
- `app/components/tables.py`
- `app/components/filters.py`
- `app/components/badges.py`
- `app/components/trust_status.py`
- `app/components/ui_framework.py`
- `app/components/human_labels.py`

## 4. Existing Outcome-Related Surfaces

Existing outcome display/status service:

- `src/services/nwr_outcome_status_display_service.py`

Existing outcome tests:

- `tests/test_nwr_outcome_status_display_service.py`
- `tests/test_outcome_column_integration_contract.py`
- `tests/test_outcome_probability_build_packet.py`
- outcome service tests under `tests/test_nwr_outcome_*`

The existing status-display service is important because it already encodes status-only safety ideas:

- probability value is null
- probability band is null
- sortable value is null
- released status is false
- app/ranking output paths are rejected
- app/ranking logic is not allowed to import the status display service

5DH does not approve using or editing this service. It only identifies it as a relevant future boundary.

## 5. Likely Schema Boundaries

Likely boundaries for any future Phase 8 app-wiring proposal:

1. app-readable status source or fixture, if HQ later authorizes one
2. app loader/service layer that reads status data
3. player table row assembly
4. player-detail card payload assembly
5. Streamlit page rendering
6. downloads/export tables
7. tests that prove no numeric or hidden fields leak

Potential existing service boundary candidates:

- `src/services/nwr_outcome_status_display_service.py`
- `src/services/nwr_outcome_release_gate_service.py`
- `src/services/table_sort_service.py`
- `src/services/ranking_surface_service.py`
- `src/services/player_detail_card_service.py`

Any future schema must be non-numeric status only and must be approved before app code is touched.

## 6. Ranking And Sorting Risk Surfaces

Ranking/sorting risks are highest around:

- `app/pages/05_rankings.py`
- `src/services/ranking_surface_service.py`
- `src/services/table_sort_service.py`
- ranking-related tests under `tests/test_ranking_*`
- player board score/row assembly services
- UI table components and Streamlit `st.dataframe` column configuration

Risk pattern:

- a future status key could accidentally become a visible sort/filter column
- status vocabulary could be converted to an ordinal value
- a hidden rank or score could be created to make status ordering deterministic
- app downloads could expose hidden model/status fields
- player-card code could show more detail than the table

Required future mitigation:

- explicit tests that `sortable_value` remains null
- no `Outcome` status sort option
- no hidden `outcome_status_priority`
- no hidden probability or band columns
- no app download/export of model internals

## 7. Hidden Sort-Key Risk

Hidden sort-key risk appears anywhere rows are normalized before display or passed to table helpers. Future audits should inspect:

- row dict construction
- dataframe columns before rendering
- dataframe columns before downloads
- table sort specs
- player-card payloads
- page session state
- cached app state

Forbidden hidden fields include:

- `outcome_probability`
- `outcome_score`
- `outcome_band`
- `outcome_rank`
- `outcome_status_priority`
- `outcome_sort`
- `hidden_outcome_sort_key`

## 8. App-Readable Output Risk

App-readable output would be risky if created under:

- `data/`
- app directories
- production/promoted artifact directories
- release-service paths
- loader inputs
- ranking/sorting pipeline paths
- downloadable current-player tables

`local_exports/` remains quarantined and must not be committed. 5DH does not create any app-readable output.

## 9. Relevant Test Locations

Potential future test locations:

- `tests/test_nwr_outcome_status_display_service.py`
- `tests/test_outcome_column_integration_contract.py`
- `tests/test_table_sort_service.py`
- `tests/test_ranking_surface_service.py`
- `tests/test_dynasty_rankings_page.py`
- `tests/test_trust_banner_ui.py`
- `tests/test_model_v4_shadow_war_board_ui.py`
- `tests/test_model_v4_app_review_service.py`

Future tests should be written before any app-wiring implementation and must prove non-numeric display, no sorting/ranking, no hidden keys, no app-readable numeric outputs, and graceful unavailable status behavior.

## 10. Numeric Display Paths

Numeric display paths remain blocked:

- exact percentages
- decimals
- odds
- coarse bands
- model scores
- rankings
- sortable values
- hidden numeric fields

The existing rankings page contains historical outcome placeholder groups and an outcome model development note. Those surfaces are high-risk for accidental numeric display and must remain blocked until HQ explicitly approves a future implementation.

## 11. Audit Result

Read-only inventory result: GREEN.

No app/source files were changed. No app-readable files were created. Numeric display paths remain blocked. The next safe sprint is a docs-only non-numeric status QA contract and test plan.

## 12. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- read-only app/source inventory completed
- `git diff --check` passed

No Python files changed in 5DH, so `python -m py_compile`, Ruff, and pytest were not required.
