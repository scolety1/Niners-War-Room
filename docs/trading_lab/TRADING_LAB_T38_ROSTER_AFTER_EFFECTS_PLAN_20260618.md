# Trading Lab T38 Roster After Effects Plan - 2026-06-18

## Goal

Convert roster aftermath from static display text into fixture-backed helper output.

## Helpers

- `estimate_keeper_impact`
- `estimate_drop_pressure_impact`
- `estimate_position_depth_impact`
- `estimate_rookie_pick_context`
- `build_roster_aftermath`

## Guardrails

- Fixture-only.
- No real roster imports.
- No Outcome, Rookie, Drop Decision, or Mock Draft imports.
- Placeholder text must say real integrations are not wired yet.

## Validation

Tests cover keeper impact, drop pressure before/after, position depth impact, rookie/mock placeholder context, and not-wired status.
