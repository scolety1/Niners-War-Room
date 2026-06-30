# Trading Lab Schedule Context Guardrail Report

Date: 2026-06-30

Verdict: `GREEN_TRADING_LAB_SCHEDULE_CONTEXT_DISPLAY_READY`

## Scope

Trading Lab now displays schedule context only as factual manual-review context inside the existing NFLVerse player context panel.

Changed behavior is limited to:

- `app/pages/23_trading_lab_v1.py`
- `src/services/trading_lab_nflverse_context_service.py`
- Trading Lab tests
- schedule-review docs

## Source Boundary

Trading Lab reads tracked repo artifacts/services only.

It does not read raw `C:\NWR_SHARED_DATA` schedule files from the app page.

## Required Filters

Schedule detail appears only when all of the following are true:

- selected asset is a player asset
- the row resolves to an approved `nwr_player_id`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- schema fields are `SAFE_NOW_DISPLAY_ONLY`
- display-only is true
- model, training, source-truth, rank, hidden-sort, trade-value, and pick-value flags are false

## Blocked Behavior

The implementation does not add:

- trade timing advice
- matchup recommendations
- buy/sell/hold recommendations
- start/sit
- schedule strength
- playoff odds
- opponent difficulty
- market, ADP, KTC, or DynastyProcess valuation logic
- least-I-can-pay logic
- automatic trade finder
- offer generator
- package fairness
- trade value delta
- pick value
- injury risk
- medical projection
- health inference
- model score
- hidden sort
- rank/source-truth changes

## Missingness

Missing or gated schedule values display as `Not enough information`.

Missing schedule context is not favorable, neutral, easy, hard, healthy, clean, safe, zero, or a recommendation.

## Identity Review

Identity-review rows expose no schedule detail. They continue to show identity-review status only.

## Pick Assets

Pick/context assets remain raw labels. They do not receive schedule context unless a future explicit approval maps them to a safe player row, and this lane does not approve that.
