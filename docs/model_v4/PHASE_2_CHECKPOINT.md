# Model v4 Phase 2 Checkpoint

Created: 2026-05-16

Phase 2 ends with a broad truth set, review-only sanity fixtures, receipt
requirements, and a truth-set coverage audit. No player formulas were rebuilt in
Phase 2. No legacy rankings were promoted. No readiness gates were unlocked.

Model v4 is ready to move into Phase 3 formula design in review-only mode.

## Phase 2 Artifacts

Truth-set universe:

- `docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.md`
- `docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv`

Sanity fixture contract:

- `docs/model_v4/SANITY_FIXTURE_CONTRACT.md`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`

Fixture runner skeleton:

- `src/services/model_v4_sanity_fixture_runner_service.py`
- `docs/model_v4/SANITY_FIXTURE_RUNNER_REPORT.md`

Receipt requirement contract:

- `docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.md`
- `docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.csv`

Truth-set coverage audit:

- `docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.md`
- `docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.csv`
- `src/services/model_v4_truth_set_coverage_audit_service.py`

## Truth Set Size And Groups

The truth set contains 80 players.

| Group | Players |
| --- | ---: |
| Niners roster | 24 |
| Elite RB controls | 9 |
| Young bridge RB controls | 1 |
| Aging RB controls | 2 |
| Elite WR controls | 9 |
| Young bridge WR controls | 3 |
| WR comparison controls | 4 |
| Aging WR controls | 7 |
| QB controls | 6 |
| TE controls | 6 |
| Low-confidence / source-gap controls | 4 |
| Incoming rookie draft-room controls | 5 |

Source priority distribution:

| Priority | Players |
| --- | ---: |
| Critical | 21 |
| High | 43 |
| Medium | 7 |
| Review | 9 |

Lifecycle distribution:

| Lifecycle | Players |
| --- | ---: |
| Established veteran | 50 |
| Year-one NFL bridge | 5 |
| Year-two NFL bridge | 10 |
| Year-three NFL bridge | 10 |
| Incoming rookie | 5 |

## Sanity Fixtures Created

The sanity fixture contract contains 29 review-only fixtures.

| Fixture Type | Count |
| --- | ---: |
| Expected ordering | 4 |
| Expected review if disagrees | 7 |
| Expected tier | 4 |
| Expected receipt explanation | 5 |
| Expected lifecycle | 3 |
| Expected suppression | 3 |
| Expected market separation | 3 |

Fixture coverage includes:

- elite RB ordering and core RB sanity checks
- elite WR tier sanity checks
- JSN vs Tee Higgins review logic
- Brian Thomas Jr. vs Luther Burden review logic
- Luther Burden vs Chase Brown review logic
- Kaleb Johnson vs useful established veterans
- aging WR vs young cornerstone RB checks
- 1QB suppression
- no-premium TE suppression
- market separation
- league-rank rule separation

## Review-Only Fixture Policy

Sanity fixture failures are review failures, not build blockers.

The runner may report:

- `ready`
- `review`
- `blocked_missing_input`
- `not_applicable_yet`

Because final Model v4 formulas and preview outputs do not exist yet, the
current fixture runner report correctly marks all 29 fixtures as
`not_applicable_yet`. It does not fake pass/fail scoring and cannot unlock
decision-ready status.

Phase 3 implication:

- Fixtures can guide formula design.
- Fixture disagreement must produce receipts and a classified review cause.
- No weight should be tuned blindly to force fixture expectations.
- A future explicit decision is required before any fixture becomes a hard gate.

## Receipt Requirements Created

The receipt requirement contract defines 11 required sections:

1. production
2. first-down scoring fit
3. usage/opportunity
4. snap/proxy role
5. projection
6. age/dropoff
7. injury/context
8. young-player prior
9. confidence
10. market context
11. league-rank rule context

Every future trusted v4 score must show:

- raw fields
- normalized fields
- source status
- contribution display
- warning display
- what happens when the section is unavailable

Critical receipt rules:

- Missing sections must be visible, not hidden behind neutral defaults.
- Market context stays separate from private football value.
- League-rank rule context stays separate from Dynasty Asset Value.
- Young-player prior must be shown separately from NFL evidence and decay.

## Coverage Audit Results

The truth-set coverage audit checked the 80-player truth set against currently
available identity, source coverage, nflverse production, first-downs, usage,
snap, projection, young bridge, market, and roster-rank context.

Readiness result:

| Status | Players |
| --- | ---: |
| Ready | 0 |
| Review | 80 |
| Blocked missing input | 0 |

No player has a hard formula-rebuild blocker. All 80 players have at least one
review warning that future receipts must show.

Coverage snapshot:

| Coverage Area | Result |
| --- | --- |
| Identity | 79 covered, 1 partial |
| Production | 35 covered, 40 partial, 5 missing |
| First-down coverage | 35 covered, 35 partial, 5 review, 5 missing |
| Usage | 35 covered, 40 partial, 5 missing |
| Snap share | 35 covered, 36 review, 9 missing |
| Projection | 36 covered, 38 review, 6 missing |
| Age/bio | 75 covered, 5 missing |
| Injury/context | 43 context-only, 32 review, 5 missing |
| Young prior | 19 covered, 6 partial, 5 review, 50 not applicable |
| Market context | 80 missing |

Primary review warnings:

- market context gaps across the full truth set
- projection gaps or local-baseline projection limitations
- injury/context gaps
- snap-share gaps
- partial production/usage/first-down coverage for players outside the v3/v3.2 safe set
- young-prior review for incoming rookie controls

## Remaining Gaps Before Formula Rebuild

These gaps do not block Phase 3 formula design, but they must remain visible:

- Market context is missing for all 80 truth-set players and must stay separate
  from private/model value.
- Route participation, routes run, TPRR, and YPRR remain unavailable from safe
  free/public structured data.
- Injury data is mostly context-only or review quality.
- Some truth-set players have partial production, first-down, usage, or snap
  coverage from current preview sources.
- Incoming rookie draft-room controls still need prospect/young-prior review
  before they can be used for strong rookie formula conclusions.
- Projection coverage is mixed and must distinguish recomputed raw-stat
  projections from local baseline or missing projection status.

## Tests Added

Phase 2 added or relies on these Model v4 test files:

- `tests/test_model_v4_sanity_fixture_runner_service.py`
- `tests/test_model_v4_receipt_requirement_contract.py`
- `tests/test_model_v4_truth_set_coverage_audit_service.py`

Together with the existing Phase 1 roster-rank contract tests:

- `tests/test_model_v4_roster_rank_contract_service.py`

The tests prove:

- the official roster-rank/top-five contract remains stable
- fixture contracts load and validate
- fixture runner output cannot unlock decision-ready status
- receipt requirement contract includes all required sections
- context-only sections remain separated from private value
- truth-set coverage audit reports the current 80-player universe
- incoming rookies are not blocked only because they lack NFL production
- core NFL players missing critical evidence are blocked in audit scenarios

## Phase 2 Confirmation

Confirmed:

- No formulas were rebuilt.
- No player scores were changed by Phase 2.
- Legacy rankings remain review-only.
- Sanity fixture failures are review failures, not build blockers.
- Receipt requirements are defined before formula work starts.
- The truth-set coverage audit found no hard formula-rebuild blockers.

Model v4 is ready for Phase 3 formula design, with one important constraint:
Phase 3 must remain review-only until formulas produce receipts that satisfy
the receipt contract and fixture disagreements are classified instead of buried.
