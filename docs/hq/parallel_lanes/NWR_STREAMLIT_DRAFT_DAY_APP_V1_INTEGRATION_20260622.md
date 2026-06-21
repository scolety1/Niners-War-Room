# NWR Streamlit Draft-Day App V1 Integration - 20260622

## Verdict

GREEN. Draft-Day Streamlit App V1 is integrated with Frozen Final Draft Board V1
and the available local-only lane prop packages.

This is not model promotion, latest_candidate approval, latest_approved approval,
private value approval, hosted deployment, public access, Mock Draft simulator
logic approval, or final trade advice.

## Source Of Truth

- Frozen board package: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622`
- Frozen board CSV: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Loaded row count: 66
- Required board fields are present.
- Hidden/private sort fields are not present.
- No lane prop may override `final_board_rank`.

## Local App

- Local URL: `http://127.0.0.1:8501/rankings`
- Fallback static export: `docs/draft_day_exports/final_board_v1_20260622/OPEN_THIS_FIRST.html`
- Local-only smoke output: `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\master_integration_smoke`

## Pages Integrated

- Live Draft Room: frozen board, session-state taken controls, best available views, risk/manual notes, mock availability props, lane status.
- Final Board / Dynasty Rankings: frozen board view at `/rankings`; legacy dynasty rankings moved to hidden legacy status.
- Player Compare: 2-4 player compare with outcome, trading, rookie, and decision prop joins when selected.
- Trading Lab: trade helper props, give/get package context, tier movement, scarcity, pick context, and verdict-band context; decision support only.
- Mock Draft: availability, pick order, and NWR pick-window props; reference only.
- Draft Prep: board/readiness checklist, prop status, frozen paths, static/zip fallback, local URL.
- Outcome Columns: outcome player context and outcome display metadata; display-only.
- Decision Board: frozen manual flags plus decision flags, manual cards, and risk-note props.
- Settings / Data Health: prop status, prop file inventory, source paths, commit, pinned hash, vendor hold, no-deploy instructions.

## Lane Prop Status

| Lane | Status | Primary file |
|---|---:|---|
| outcome_columns | GREEN | `outcome_player_context.csv` |
| trading_lab | GREEN | `trade_helper_context.csv` |
| rookie_hq | GREEN | `rookie_overlay_context.csv` |
| mock_draft | GREEN | `availability_context.csv` |
| decision_board | GREEN | `decision_flags_context.csv` |

## Remaining YELLOW-HOLD

- Vendor research remains YELLOW-HOLD and is not a safe board signal.
- Trading Lab remains decision-support only and does not produce final trade advice.
- Mock Draft remains reference-only; simulator logic was not changed.
- Display-only prop fields remain display-only.

## Smoke Test

Browser smoke rendered all V1 pages without exception and found the frozen-board
source badge on each page:

- `/rankings`
- `/live-draft-room`
- `/player-compare`
- `/trading-lab`
- `/mock-draft`
- `/draft-room`
- `/outcome-columns`
- `/decision-board`
- `/settings`

Focused pytest and Ruff passed for the app/service/test files touched by this
integration.

## Guardrails

- No tuning was rerun.
- No `latest_candidate` or `latest_approved` pointer was updated.
- Frozen board and pinned snapshot were not mutated.
- No `C:\NWR_SHARED_DATA` contents are committed.
- No raw vendor CSVs or raw predictions are committed.
- No hidden sort fields were created.
- No new port was exposed beyond the existing local Streamlit app.
- No deployment, hosted/public access, or GitHub Pages setup was performed.
