# NWR Streamlit Draft-Day App V1 Contract - 20260622

## Verdict

GREEN for app-foundation wiring. The connected Streamlit app now routes the visible
draft-day surfaces through Frozen Final Draft Board V1 as the source of truth.

This is not model promotion, latest_candidate approval, latest_approved approval,
hosted deployment, Mock Draft simulator logic approval, private value approval, or
final draft advice.

## Local App

- Entry point: `app/main.py`
- Local URL: `http://127.0.0.1:8501/rankings`
- Run command: `streamlit run app/main.py`
- Frozen local board source: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Repo-safe fallback copy: `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`

## Source-Of-Truth Rule

Every visible draft-day page must either:

- read from Frozen Final Draft Board V1,
- read from a lane prop/context file that references Frozen Final Draft Board V1, or
- show a clear MISSING/YELLOW-HOLD state.

No page may override `final_board_rank`, `final_tier`, `position_rank`,
`model_posture_used`, `candidate_status`, `risk_notes`, or
`needs_manual_review`.

## Pages Wired

- Live Draft Room: frozen-board best available view with local session-state taken marking.
- Final Board / Dynasty Rankings: frozen-board table at `/rankings`; legacy dynasty rankings are hidden/hold.
- Player Compare: 2-4 player compare from frozen board with optional lane props.
- Trading Lab: package compare shell using board rank/tier/visible scores as context only.
- Mock Draft: reference-only shell; simulator logic is unchanged.
- Draft Prep: checklist, paths, row-count checks, lane prop status.
- Outcome Columns: display-only shell; YELLOW-HOLD until outcome props exist.
- Decision Board: manual review flags and risk notes from frozen board.
- Settings / Data Health: source paths, pinned hash, lane prop status, vendor hold/no-deploy status.

## Local-Only Prop Contract Root

`C:\NWR_SHARED_DATA\draft_day_app_props\20260622`

Created local-only contract files:

- `APP_PROP_CONTRACT.md`
- `APP_PROP_MANIFEST_TEMPLATE.csv`
- `outcome_columns_contract.md`
- `trading_lab_contract.md`
- `rookie_hq_contract.md`
- `mock_draft_contract.md`
- `decision_board_contract.md`

Expected lane folders:

- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\outcome_columns`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\trading_lab`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\rookie_hq`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\mock_draft`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\decision_board`

## Missing Props

The app intentionally treats missing lane props as YELLOW-HOLD rather than as a
board blocker:

- Outcome Columns props: missing/YELLOW-HOLD.
- Trading Lab props: missing/YELLOW-HOLD.
- Rookie HQ props: missing/YELLOW-HOLD.
- Mock Draft props: missing/YELLOW-HOLD.
- Decision Board props: missing/YELLOW-HOLD.

## Guardrails

- No tuning was rerun.
- No `latest_candidate` or `latest_approved` pointer was updated.
- Pinned snapshot is read-only and must remain unchanged.
- Mock Draft simulator logic was not changed.
- No vendor fields are used as safe model signals.
- ADP, market, rankings, projections, and trade calculator context may only be display-only.
- No hidden sort fields are allowed.
- `C:\NWR_SHARED_DATA` contents remain local-only and are not committed.
- No raw vendor CSVs, raw prediction dumps, or private value exports are committed.
- No deploy, hosted/public access, exposed port change, or GitHub Pages setup is approved.
