# Trading Lab T24 Fake Package Engine Plan

Date: 2026-06-18

## Goal

Create a deterministic fake/in-memory package generator so the Trade Lab UI can
show varied fantasy trade package examples before real data integration.

## Scope

- Add fake trade-for, trade-away, upgrade-position, pick-conversion, and
  drop-pressure packages.
- Add package sorting by NWR gain, realism, and roster impact.
- Use fake names only.

## Fake Names

Target Player, Player A, Player B, Player C, Player D, 2026 2nd, 2026 3rd,
Team Alpha, Team Bravo, Team Charlie.

## Guardrails

No files, APIs, real data imports, public trade-value fetches, generated
outputs, or Wall Street language.
