# Drop Decision Phase 5B Authorization Decision Packet - 2026-06-15

## Status

This packet is for Main HQ review only. It does not authorize Phase 5B by itself.

Current baseline:

- Branch: `work/drop-decision-day-review`
- HEAD: `47751a99c409c100152e814b34fddccdf6170c22`
- Commit: `47751a9 Document drop decision Phase 5A readiness`
- Phase 5A status: committed GREEN for human-review context

Phase 5B recommendation-mode remains closed unless Main HQ manually pastes a separate future authorization prompt.

## What Phase 5B Would Mean

Phase 5B would be a separate decision-support mode after human review. It would require Main HQ to explicitly define the permitted scope, gates, stop rules, allowed outputs, forbidden outputs, and rollback criteria.

Phase 5B would not be an automatic roster-action mode. Human approval would still be required for any real roster move.

## What Phase 5B Would Still Not Allow Unless Explicitly Authorized

Even if Main HQ later authorizes a Phase 5B plan or run, the following remain blocked unless specifically and safely authorized in that later prompt:

- app-readable recommendation outputs
- probabilities
- outcome bands
- promoted artifacts
- push or deploy
- `data/` commits
- `local_exports/` commits
- rookie framework edits
- external/ranking/projection source use
- automatic roster actions

## Outputs Forbidden In The Current Phase 5A Lane

The current lane cannot produce:

- final or implied drop recommendations
- named final cut/keep decisions
- sorted or ranked drop-candidate lists
- probability outputs
- outcome-band outputs
- app-readable recommendation artifacts
- promoted outputs
- deployments

## Gates That Must Be GREEN Before Any Future Phase 5B

Before Main HQ considers a separate Phase 5B authorization, the following should remain GREEN:

- clean branch and committed Phase 5A baseline
- Decision Board usable as human-review context
- human-review prep artifacts present and local-only
- `local_exports` ignored and not staged
- no tracked docs drift from generators
- Phase 5A handoff reviewed by Main HQ
- required Phase 5A tests passing
- age provenance caveat acknowledged
- blocked outputs and stop rules explicitly repeated in the future prompt

## Phase 5A Caveats To Carry Forward

- The age source is user/source-provided as of June 4, 2026.
- Age values are source-provided strings, not DOB-derived values.
- Do not recalculate ages to today.
- Do not use DOBs, public rankings, projections, ADP, trade calculators, RotoWire values/outlooks/rankings/projections, external sources, or same-season final stats to alter the age artifact.
- Age coverage remains partial against prospect rows.
- Review-band fields are human-review context labels, not outcome bands.
- Local artifacts remain ignored local review artifacts.

## Main HQ Decision Options

### Option A - Stay Phase 5A Only

Use this if Main HQ wants to continue artifact review without any decision-support mode:

```text
Main HQ keeps Drop Decision in Phase 5A only. Do not open Phase 5B. Continue to use artifacts only as human-review context. Do not produce final/implied recommendations, candidate sorting/ranking, probabilities, bands, promoted artifacts, or app-readable recommendation outputs.
```

### Option B - Request A Phase 5B Plan Only

Use this if Main HQ wants Codex to draft gates and stop rules but not execute decision support:

```text
Main HQ requests a Drop Decision Phase 5B decision-support plan only. Do not execute Phase 5B. Draft the proposed gates, allowed outputs, forbidden outputs, evidence requirements, and rollback criteria. Do not name final drop candidates, sort/rank candidates, create probabilities/bands, or produce recommendations.
```

### Option C - Future Phase 5B Authorization Template

The following wording is not active unless Main HQ manually pastes it in a later prompt:

```text
Main HQ explicitly authorizes a separate Drop Decision Phase 5B decision-support run. This authorization permits a review-only decision-support analysis under the gates and stop rules stated in this prompt. It still does not permit app-readable recommendation outputs, probabilities, outcome bands, promoted artifacts, push, deploy, data/local_exports commits, or automatic roster actions. Human approval remains required for any actual roster move.
```

A future Phase 5B prompt should include exact files to inspect, allowed output format, forbidden wording, stop conditions, and whether any final recommendation wording is permitted. Without those details, Codex should keep Phase 5B closed.

## Confirmation

This packet does not open Phase 5B. It provides Main HQ with decision wording for a future prompt only.

No final or implied recommendation, ranking/sorting change, probability, band, app-readable recommendation output, promoted artifact, push, deploy, `data` commit, `local_exports` commit, rookie framework edit, forced rookie/veteran merge, or external/ranking/projection source use is authorized by this packet.
