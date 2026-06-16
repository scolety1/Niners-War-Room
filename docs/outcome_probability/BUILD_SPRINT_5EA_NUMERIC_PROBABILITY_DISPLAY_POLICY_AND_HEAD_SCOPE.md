# Sprint 5EA - Numeric Probability Display Policy And Head Scope

## Purpose

Sprint 5EA defines the controlled policy for moving the Outcome lane from the existing non-numeric status foundation toward future displayed numeric probabilities on the Rankings page.

This sprint is a policy and scope gate only. It does not create current-player inference, probability artifacts, app-readable outputs, UI/source wiring, rankings/sorting behavior, hidden sort keys, promoted artifacts, pushes, deploys, or releases.

## Intended Future Display Universe

The Rankings page is the intended player universe for any future numeric Outcome probability display. Future display work must attach to the existing Rankings page player pool and must not invent a separate current-player universe.

Before any numeric display can be proposed, later gates must discover the Rankings page player pool, identify a stable join key, validate current-player feature coverage, run a quarantined local-only dry run, and pass artifact/human-review audits.

## Target First Numeric Display Heads

The Phase 10 target first numeric display head set is:

| Head | Initial status | Notes |
| --- | --- | --- |
| `qb_t12` | target | Accepted Phase 6 head for future display planning. |
| `rb_t12` | target | Accepted Phase 6 head for future display planning. |
| `rb_t24` | HQ-requested gated target | Not in the final safest Phase 6 accepted display set; must pass Sprint 5EC before inclusion in a local dry run or future display set. |
| `wr_t12` | target | Accepted Phase 6 head for future display planning. |
| `wr_t24` | target | Accepted Phase 6 head for future display planning. |
| `wr_t36` | target | Accepted Phase 6 head for future display planning. |
| `te_t12` | target | Accepted Phase 6 head for future display planning. |

`rb_t24` must not be silently included. If Sprint 5EC cannot upgrade it to GREEN, it must either remain excluded from the first numeric set or the packet must stop and report the blocker.

## Exact Percentage Display Policy

Exact numeric display is not allowed in this sprint. Future exact percentage display may be considered only after later inference, artifact audit, human review, app-readable artifact contract, and app-wiring gates pass.

No current-player probabilities are generated here. No exact display percentages are created, committed, promoted, or wired into the app.

## Rounding Policy Proposal

If a later approved display sprint reaches numeric UI work, the first numeric display should use integer percentages only.

Rules proposed for later gates:

- no decimal percentages;
- no hidden higher-precision app fields;
- no app-readable high-precision probability columns that are merely rounded at render time;
- audit evidence may retain local-only probability units, but committed app-facing artifacts must not expose hidden precision.

## Low-Confidence And Null Policy

Unsupported players, rows with missing required features, rookies that are not eligible for veteran heads, blocked positions, and rows that fail join or provenance checks must not be displayed as `0%`.

Future UI behavior should use `unavailable` or no number for unsupported rows. Local-only dry-run evidence may include unavailable reasons, but those reasons must not become hidden ranking or sorting fields.

## Sorting And Hidden Key Policy

Outcome probabilities must not drive rankings or sorting in the first numeric display release.

Blocked:

- sorting by Outcome probability;
- ranking by Outcome probability;
- hidden sort keys derived from Outcome probability;
- ranking deltas or tie-breakers derived from Outcome probability;
- promoted artifacts intended for rankings/sorting pipelines.

## App/UI Policy For This Sprint

No app UI, component, service, loader, or source files are edited in Sprint 5EA. No app-readable probability, band, or status artifact is created.

## Recommendation

Verdict: GREEN for proceeding to Sprint 5EB Rankings page player pool and join key discovery.

Rationale:

- the target head list is explicit;
- `rb_t24` is gated rather than assumed safe;
- exact percentages remain blocked until later gates;
- local-only probability evidence is not created yet;
- app-readable output and UI/source wiring remain blocked;
- rankings/sorting and hidden sort keys remain blocked.

## Release Stance

Sprint 5EA does not approve display implementation. It only approves read-only discovery of the Rankings page player pool and join contract in Sprint 5EB.
