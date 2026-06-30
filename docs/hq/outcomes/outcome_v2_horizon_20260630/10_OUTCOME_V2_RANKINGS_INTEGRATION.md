# Outcome V2 Rankings Integration

Date: 2026-06-29

## 1. Executive Decision

`GREEN_OUTCOME_V2_RANKINGS_OUTCOME_LENS_INTEGRATION`

Outcome V2 current-player display context is integrated into Dynasty Rankings only through the Outcome Lens / outcome-column display path.

No Dynasty Rank, tiers, Final Board Rank, Candidate Rank, model logic, source truth, hidden sort, trade value, pick value, Live Draft, Mock Draft, or draft runtime behavior was changed.

## 2. Artifact Used

Committed compact artifact:

`docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display.csv`

Source artifact branch:

`origin/work/outcome-v2-current-display-artifact-20260630`

Artifact summary:

| Metric | Value |
| --- | ---: |
| Rows | 240 |
| Rows with validated probabilities | 184 |
| Rows with all probabilities as `Not enough information` | 56 |
| Rookie/prospect rows out of scope | 43 |
| Missing veteran feature rows | 5 |
| Validated display fields | 34 |

## 3. Fields Displayed

Outcome V1 / Legacy fields remain available:

- `QB T12`
- `RB T12`
- `RB T24`
- `WR T12`
- `WR T24`
- `WR T36`
- `TE T12`

Outcome V2 validated fields are displayed with `Outcome V2 / Display-Only` labels:

- QB T6/T12 This Year, Next Year, Within 5Y
- RB T6/T12/T24/T36 This Year
- RB T6/T12/T24/T36 Next Year
- RB T24/T36 Within 5Y
- WR T6/T12/T24/T36 This Year
- WR T6/T12/T24/T36 Next Year
- WR T6/T12/T24/T36 Within 5Y
- TE T6/T12 This Year, Next Year, Within 5Y

Outcome V2 status/caveat columns shown in the Outcome Lens:

- `Outcome V2 Status (Display-Only)`
- `Outcome V2 Availability Caveat`
- `Outcome V2 Caveat`

## 4. Fields Blocked

Blocked weak-calibration fields are not emitted as probability columns:

- `RB_T6_WITHIN_5Y`
- `RB_T12_WITHIN_5Y`

The Outcome Lens callout lists those fields as blocked / `Not enough information`.

## 5. Missing-Data Behavior

Missing or unvalidated Outcome V2 data displays as:

`Not enough information`

It never displays as `0%`, `false`, or an implied miss.

The five veteran rows with missing 2025 feature coverage remain `missing_current_feature_coverage`:

- Brandon Aiyuk
- Joe Mixon
- Tank Dell
- Jonathon Brooks
- MarShawn Lloyd

Rookies/prospects remain `out_of_scope_rookie_or_prospect`.

## 6. Scoring / As-Of Caveats

Displayed in the Outcome Lens:

- `This Year = 2026 NFL season`
- `Scoring caveat: partial exact first-down scoring; sack_fumbles_lost missing`
- `Missing data is Not enough information, not low probability`

## 7. Availability Caveat

Displayed in the Outcome Lens:

- `Availability caveat: games field missing; no row is Not enough information, not clean health`

The integration does not create injury risk, medical projection, recovery projection, or health assumptions.

## 8. Guardrails

Outcome V2 is display-only.

It does not drive:

- Dynasty Rank
- tiers
- Final Board Rank
- Candidate Rank
- hidden sort
- model logic
- source truth
- trade value
- pick value
- Live Draft decisions
- Mock Draft behavior

Blocked inputs remain unused:

- DynastyProcess
- ADP
- market values
- CFBD
- Gmail
- vendor/RotoWire/FantasyPros
- projections
- analyst ranks
- trade values
- true routes / TPRR / YPRR
- injury projections
- medical recovery assumptions
- rookie/prospect college data

## 9. UI Behavior

Clean Board remains clean because the page keeps `outcome_mode=Hide` for that preset.

Outcome Lens uses the existing primary player board table, not a second disconnected table.

Default full-board sort remains Dynasty Rank ascending.

Market columns remain display-only.

Outcome V1 remains available as legacy display context in the same Outcome Lens path.

## 10. Human Review Checklist

- Open `/rankings`.
- Select `Outcome Lens`.
- Confirm the main table remains one primary player board.
- Confirm the page shows the Outcome V2 display-only callout.
- Confirm `This Year = 2026 NFL season`.
- Confirm the scoring and availability caveats are visible.
- Confirm missing data says `Not enough information`.
- Confirm rookies/prospects are marked out of scope or not enough information.
- Confirm RB T6/RB T12 Within 5Y are not shown as probability columns.
- Confirm Clean Board hides Outcome columns.
- Confirm default full-board sort remains Dynasty Rank.
