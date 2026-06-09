# RotoWire Golden Build Checkpoint

Date: 2026-05-17

Status: review-only checkpoint

## Summary

The overnight build moved Model v4 from a raw RotoWire stats-first layer into a
review-only dynasty candidate layer with first-down-aware replacement/VORP
context, age/dropoff controls, receipt rows, named-player review, and sanity
review.

Nothing was promoted into the active app model.

## Built

### Replacement Baselines

Output:

`local_exports/model_v4/rotowire_replacement/latest/`

Current replacement rows:

| Position | Replacement rank | Replacement player | Base points | Estimated first-down points | First-down-adjusted base |
| --- | ---: | --- | ---: | ---: | ---: |
| QB | 10 | Jared Goff | 245.6333 | 3.0852 | 248.7185 |
| RB | 36 | J.K. Dobbins | 96.9 | 15.7232 | 112.6232 |
| WR | 34 | Keenan Allen | 93.7 | 18.5711 | 112.2711 |
| TE | 10 | Colston Loveland | 95.1 | 13.7956 | 108.8956 |

Important limitation: current baselines are first-down-aware, but the 2025
rushing/receiving first downs are estimated from 2022-2024 direct nflverse
history. They are labeled `estimated_from_history` and remain review-only until
audited.

### VORP Review Layer

Output:

`local_exports/model_v4/rotowire_vorp_review/latest/`

Rows generated:

- 80 VORP rows
- 37 positive VORP players

Private value guardrails:

- projections used for core value: false
- market used for private value: false
- league rank used for private value: false

### Dynasty Candidate Layer

Output:

`local_exports/model_v4/rotowire_dynasty_candidate/latest/`

Rows generated:

- 80 candidate rows
- 480 component rows
- 480 receipt rows
- 187 warning rows

The layer combines:

- stats-first evidence
- replacement/VORP review logic
- position-specific weights from Deep Research
- route/target role where licensed RotoWire exports support it
- age/dropoff caps
- confidence caps for missing evidence

It does not use projections, ADP, market, rankings, or league rank for private
football value.

Post-review correction: confidence is now cap/receipt-only and does not add
positive private football value. Missing component evidence is displayed as
missing with blank score/contribution instead of numeric zero evidence.

## Key Review Outcomes

### Supported

- Bijan Robinson and Jahmyr Gibbs are RB1/RB2.
- De'Von Achane is RB5 and no longer resembles a legacy `bubble` player.
- Lamar Jackson is suppressed below Achane in this 10-team 1QB review.
- Derrick Henry, Christian McCaffrey, Saquon Barkley, Keenan Allen, Davante
  Adams, and other age-cliff players are capped instead of being boosted by
  historical production alone.
- Brock Bowers remains outside the overall top 20 in no-TE-premium review.
- Jeremiyah Love remains `weak_review` until sourced rookie/prospect evidence
  exists.

### Needs Review

- Malik Nabers is WR19 in the current candidate layer, which conflicts with the
  elite-WR sanity fixture and requires receipt review before any formula patch.
- Brian Thomas Jr. is WR22 and Luther Burden is WR33. This may be evidence-led
  given current RotoWire role data, but it should be audited because both are
  important Niners roster decision names.
- Lamar Jackson is QB4 and overall 49 in the current candidate layer. His
  replacement/VORP receipt is negative against the 10-team 1QB QB replacement
  baseline, while his remaining premium depends heavily on rushing separation.
  This should be audited as a potential sell-high/trade-review case rather than
  treated as a simple hold/drop answer.
- Current replacement/VORP logic is first-down-aware but depends on clearly
  labeled historical first-down estimates for 2025.
- Incoming rookie/prospect data is not integrated into the candidate layer.
- Injury severity remains visible as context, but no robust medical risk model
  has been promoted.

## Named-Player Audit Outputs

Generated:

- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.csv`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.md`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.csv`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.md`

Sanity review result:

- ready: 12
- review: 1
- blocked: 0

The single review fixture is Malik Nabers outside the expected high WR tier.

## First-Down-Aware Implementation

Created:

`docs/model_v4/ROTOWIRE_FIRST_DOWN_AWARE_REPLACEMENT_PLAN.md`

Implemented review-only outputs now confirm:

- RotoWire player-stat exports currently do not provide direct
  rushing/receiving first-down fields.
- Direct first-down history uses source-safe nflverse import rows for
  2022-2024.
- Estimated first downs must be labeled `estimated_from_history`.
- Estimated first downs may not masquerade as direct data.

## Current Decision

Model v4 is not ready for active app promotion.

It is ready for an external audit focused on formula balance, receipt support,
first-down estimation honesty, and remaining source gaps.

## External Audit Packet

Generated after this checkpoint:

`local_exports/model_v4/audit_packets/rotowire_golden_candidate_external_audit_20260517_043643.zip`

The packet contains derived review-only outputs, docs, selected implementation
files, and selected tests. It intentionally excludes raw licensed RotoWire
exports.

## Verification

Focused tests passed:

```text
tests/test_model_v4_rotowire_replacement_baseline_service.py
tests/test_model_v4_rotowire_vorp_review_service.py
tests/test_model_v4_rotowire_dynasty_candidate_service.py
```

Ruff passed on the dynasty candidate audit script before generation.

Full verification passed after the first-down implementation:

```text
focused tests: 18 passed
pytest: 907 passed
ruff check .: all checks passed
```

Ruff emitted access-denied warnings for temporary folders, but returned success
and reported no lint failures.
