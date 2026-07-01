# Experiment-Only Gate Requirements

Verdict: `YELLOW_REQUIREMENTS_DEFINED_NO_EXPERIMENT_APPROVAL`

This packet does not approve any experiment. It defines the minimum gates that must pass before a future lane can even ask for sandbox or shadow experiment approval.

## Universal Requirements

Every feature family must provide:

- exact prediction anchor;
- point-in-time source snapshot;
- source extraction timestamp;
- feature as-of timestamp;
- identity-safe join audit;
- missingness and censoring policy;
- leakage diagnostics;
- label interaction audit;
- row counts by season, position, and feature state;
- blocked-source scan;
- explicit approval boundary.

## Experiment-Only Boundary

An experiment-only approval, if a future lane ever earns it, would still not approve:

- production model use;
- training truth promotion;
- source-truth promotion;
- app behavior;
- active probabilities;
- Rankings integration;
- Gate G;
- hidden sort;
- trade value;
- pick value;
- recommendations.

## Required Feature-Specific Gates

- Roster and weekly roster: point-in-time roster event and season-week replay gate.
- Injury and practice: publication timing, game-week anchor, and no-medical-projection gate.
- Schedule: schedule release/update as-of gate and no matchup-strength gate.
- Depth chart: depth chart publication, role semantics, and post-draft-only anchor gate.
- Snap and last active fields: closed-week lag, usage window, and career-survival censoring gate.
- Draft capital: draft date, drafted-only admission, and post-draft-only feature split.
- Combine: event-date coverage, identity, and feature coverage gate.
- Player stats sidecar: historical sidecar builder and label parity gate.
- Availability denominator: rostered-game denominator, active/inactive hierarchy, and missingness gate.
- CFBD and UDFA: explicit source-policy and human-review gates.

## Current Result

No row in the readiness matrix satisfies the experiment-only gate. `APPROVED_FOR_EXPERIMENT_ONLY` count remains `0`.
