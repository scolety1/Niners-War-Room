# Trading Lab T21D UI Component Plan

Date: 2026-06-18

## Purpose

T21D implements the safest desktop-first Trade Lab UI surface using fake,
in-memory fantasy trade data.

## App Convention Inspection

The repo has an obvious Streamlit page convention under `app/pages/`. T21D may
therefore add one isolated Trade Lab page file without touching navigation or
unrelated app files.

## Implementation Plan

- Add reusable UI labels/sections/render helper under `src/trading_lab/`.
- Add one isolated Streamlit page at `app/pages/11_trade_lab.py`.
- Use fake demo packages from the T21C model.
- Add focused tests for labels, sections, fantasy orientation, formatting, and
  route status.

## Guardrails

No data ingestion, real source integration, app-wide navigation edits, generated
outputs, deployment, automated trade submission, or old Wall Street framing.
