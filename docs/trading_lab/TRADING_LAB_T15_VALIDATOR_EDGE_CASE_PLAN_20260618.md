# Trading Lab T15 Validator Edge Case Plan

Date: 2026-06-18

## Purpose

T15 hardens Trading Lab validation-only helpers against edge cases while keeping
all behavior in-memory and paper/research-only.

## Safe Changes

- Add punctuation-tolerant prohibited phrase patterns.
- Traverse nested in-memory manual artifact payload text.
- Traverse nested config list values for prohibited text and secret-like values.
- Add tests for mixed case, punctuation, nested payloads, missing required
  values, unsupported artifact types, and ambiguous future-phase HOLD behavior.

## Not Allowed

- No dependencies.
- No file I/O.
- No network calls.
- No market-data fetching.
- No broker/API integration.
- No execution or simulation objects.
- No app, deployment, or fantasy-lane changes.

## Verdict Rule

GREEN if focused Trading Lab pytest, Ruff, and Git diff checks pass.
