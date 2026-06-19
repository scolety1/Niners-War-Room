# Trading Lab T28 Bad Trade Detector Plan

Date: 2026-06-18

## Goal

Make warning labels clear and useful in the fake-data Trade Lab UI.

## Warning Coverage

- Market fair but NWR negative
- NWR positive but unrealistic
- Worse drop pressure
- Hurts keeper structure
- Gives scarce position depth
- Opponent has no reason to accept
- Public fantasy market source missing/stale
- Includes untouchable player
- Overpays for aging production
- No real integration yet

## Guardrails

Warnings support manual fantasy trade review only. They do not submit offers,
automate decisions, ingest data, or use real integrations.
