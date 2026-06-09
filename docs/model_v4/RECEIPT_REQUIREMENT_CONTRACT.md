# Model v4 Receipt Requirement Contract

Created: 2026-05-16

This contract defines what a Model v4 receipt must show before any score can be
trusted. It does not change formulas, readiness gates, player values, or UI
decision labels. It is the receipt standard that future scoring work must meet.

Machine-readable file:

- `docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.csv`

Authoritative context:

- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.md`
- `docs/model_v4/LEAGUE_RULES_LOCK.md`
- `docs/model_v4/OFFSEASON_RANKING_SHEET_LOCK.md`

## Receipt Policy

Every trusted v4 score must be explainable from raw evidence through normalized
feature value to contribution. If a section is missing, imputed, proxy-only, or
context-only, that state must be visible in the receipt. Hidden defaults cannot
stand in for real football evidence.

Receipts must keep these lanes separate:

- private football/model value
- confidence and data-quality penalties
- market/trade context
- league-rank rule context
- young-player prior context

Market values and league-rank rule mechanics may explain trade or forced-release
context, but they must not be shown as private football value contributions.

## Required Receipt Sections

| Section | Purpose |
| --- | --- |
| `production` | Show real NFL production and LVE scoring production evidence. |
| `first-down scoring fit` | Show rushing and receiving first-down evidence tied to the 0.4 LVE rule. |
| `usage/opportunity` | Show targets, carries, shares, red-zone use, goal-line use, and opportunity. |
| `snap/proxy role` | Show snap share as a role proxy without pretending it is route participation. |
| `projection` | Show projection source, raw projected stats, and recomputed LVE points. |
| `age/dropoff` | Show age, years of experience, position bucket, and dropoff context. |
| `injury/context` | Show injury information as context and confidence effect, not fake production. |
| `young-player prior` | Show draft/prospect prior separately from NFL evidence and decay weight. |
| `confidence` | Show why the model is strong, usable, review, weak, or blocked. |
| `market context` | Show trade market and liquidity separately from private value. |
| `league-rank rule context` | Show the top-five rule context separately from player quality. |

## Required CSV Fields

Each row in `RECEIPT_REQUIREMENT_CONTRACT.csv` includes:

- `receipt_section`
- `required_raw_fields`
- `normalized_fields`
- `source_status`
- `contribution_display`
- `warning_display`
- `when_section_unavailable`

The field lists use `|` separators so later receipt builders can parse them
without ambiguity.

## Trust Rules

### Raw To Normalized To Contribution

Every scoring section must show:

- the raw values used
- the source status of those values
- the normalized field or component score
- the contribution to the relevant score
- the warning state if values are missing, stale, estimated, or proxy-only

### Missing Sections

Unavailable sections must be displayed as unavailable. They must not disappear
silently, and they must not be filled with neutral values that look like real
evidence.

### Context-Only Sections

`injury/context`, `market context`, and `league-rank rule context` can explain
decisions, confidence, and opportunity. They cannot directly increase private
football value unless a later signed-off contract explicitly changes that rule.

### Young Players

Young-player receipts must separate:

- draft capital and prospect prior
- prior decay weight
- NFL evidence weight
- final bridge contribution

This is the guardrail against blindly boosting young players or burying useful
young players because the prior is invisible.

## Phase 2D Status

This is a contract-only phase. Final Model v4 formulas do not exist yet, so this
file defines the receipt surface those formulas must satisfy later.
