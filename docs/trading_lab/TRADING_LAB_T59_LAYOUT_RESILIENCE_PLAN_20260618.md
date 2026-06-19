# Trading Lab T59 Layout Resilience Plan - 2026-06-18

## Goal

Make desktop helper output resilient to long names, many warnings, missing packages, many rows, long notes, and placeholder provider states.

## Helpers

- Long asset name formatter.
- Warning stack formatter.
- No-package layout message.
- Compact negotiation note.
- Compact package row.
- Provider status panel labels.

## Guardrails

- Fixture-only.
- No real data assumptions.
- No generated outputs.

## Validation

Tests cover long names, warning stacks, no-package fallback, multiple rows, and placeholder provider labels.
