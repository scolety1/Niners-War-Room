# Model v4 Sanity Fixture Contract

Created: 2026-05-16

This contract turns the Model v4 football sanity beliefs into review-only
fixtures. These fixtures are not manual rankings and they are not formula
overrides. They define what the future Model v4 fixture runner must inspect,
explain, and report when v4 preview scores exist.

Machine-readable file:

- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`

Authoritative context:

- `docs/model_v4/FOOTBALL_SANITY_BELIEFS.md`
- `docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`
- `docs/model_v4/LEAGUE_RULES_LOCK.md`

## Review-Only Policy

Fixture failures are review failures, not build blockers, unless a later phase
explicitly promotes a fixture to blocking status.

The fixture runner should report disagreement as:

- data gap
- identity issue
- lifecycle issue
- normalization issue
- formula review
- acceptable model disagreement
- missing receipt evidence

The runner must not silently tune weights to force these expectations. If the
model disagrees, the correct response is to show the receipts and classify the
cause.

## Fixture Types

| Fixture Type | Meaning |
| --- | --- |
| `expected_ordering` | Expected relative order or broad hierarchy. Disagreement requires receipt review. |
| `expected_tier` | Expected broad tier such as elite/core/review-only. Disagreement requires explanation. |
| `expected_review_if_disagrees` | Flexible sanity check where disagreement is allowed but must be explained. |
| `expected_receipt_explanation` | Requires specific receipt components to be visible. |
| `expected_lifecycle` | Requires correct incoming rookie / young bridge / established veteran treatment. |
| `expected_suppression` | Requires position-scarcity suppression such as 1QB or no-premium TE. |
| `expected_market_separation` | Requires market or rule context to stay out of private football value. |

## Required CSV Fields

Each fixture row includes:

- `fixture_id`
- `fixture_name`
- `fixture_type`
- `players`
- `expected_behavior`
- `review_severity`
- `receipt_requirement`
- `football_logic`

The `players` field uses `|` separators so fixture runners can parse the player
list without ambiguity.

## Fixture Coverage

The contract includes fixtures for:

- Bijan / Gibbs / Achane / McCaffrey / Kyren / Jeanty
- JSN / Puka / Chase / Jefferson / Amon-Ra / Lamb / Nabers
- JSN vs Tee Higgins
- Brian Thomas Jr. vs Luther Burden
- Luther Burden vs Chase Brown
- Kaleb Johnson vs useful established veterans
- aging WRs vs young cornerstone RBs
- 1QB suppression
- no-premium TE suppression
- market value separation
- league-rank rule separation
- low-confidence source-gap controls
- route-data unavailability
- incoming rookie lane separation

## Guardrails

1. Do not tune formulas from this contract alone.
2. Do not treat a sanity belief as a cited factual source.
3. Do not let market value move private value.
4. Do not let league rank move Dynasty Asset Value.
5. Do not let route metrics appear as real evidence without an approved
   structured source.
6. Do not let young-player draft capital score established veterans.
7. Do not let low-confidence rows become trusted decisions without receipts.

## Phase 2B Exit Criteria

- The fixture contract exists in markdown and CSV.
- Every requested fixture type is represented.
- Every requested named fixture family is represented.
- Failures are defined as review findings, not build blockers.
- No formulas have changed.

## Next Step

Phase 2C should add a fixture runner skeleton that can load this contract,
validate the schema, detect missing players or unavailable model outputs, and
produce review-only statuses without pretending final v4 formulas exist.

