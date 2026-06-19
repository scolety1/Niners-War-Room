# Trading Lab T32 UI MVP Freeze Plan - 2026-06-18

## Starting Head

T32 starts from `9b81c62495d0948f3f423c7c5ec7dcb10d7bd3aa`, the GREEN T31 placeholder boundary commit.

## Goal

Freeze the fake-data desktop Trade Lab UI MVP and prepare it for Master/user review.

## Scope

- Docs-only freeze packet.
- No real data integration.
- No app shell or navigation changes.
- No generated outputs.
- No deployment.

## Review Target

- Isolated routed Streamlit page: `app/pages/11_trade_lab.py`
- Component: `src/trading_lab/trade_lab_component.py`
- Fake package helpers: `src/trading_lab/trade_lab_ui.py`

## Validation Plan

- Run all focused Trading Lab tests.
- Run Ruff over Trading Lab source, tests, and isolated page.
- Run `git diff --check`.
- Confirm final status is clean after commit/push.
