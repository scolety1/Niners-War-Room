# Project Gold Sprint 2 / Phase 8 Audit: Age And Dropoff Sanity

Date: 2026-05-14

## Scope

This audit checks whether the new age/dropoff layer behaves visibly and safely before any ranking trust is restored. Rankings remain review-only.

Audit artifacts were written to:

`local_exports/model_audits/sprint2_phase8_age_dropoff_sanity_20260514`

Files:

- `age_dropoff_sanity_audit.csv`
- `age_dropoff_sanity_summary.csv`
- `top_rbs_by_age_bucket.csv`
- `top_wrs_by_age_bucket.csv`
- `top_qbs_by_age_bucket.csv`
- `top_tes_by_age_bucket.csv`
- `age_review_flags.csv`
- `manifest.json`

## Result

Age/dropoff is now visible, sourced, and not duplicated.

Summary:

- Active player rows audited: 1,039
- Age source status: 1,039 `derived_real_data`
- Age/bio source coverage: 1,039 `ready`
- Hidden age flags: 0
- Duplicate age contribution flags: 0
- Age buckets:
  - `prime_window`: 656
  - `mild_decline`: 220
  - `cliff_risk_window`: 163

## Position Sanity Notes

### RB

Older RBs are being flagged and penalized:

- James Cook and Najee Harris are in `mild_decline`.
- Josh Jacobs, Saquon Barkley, Derrick Henry-type profiles, and other late-age RBs are in `cliff_risk_window`.
- RB age + injury/workload fragility flags are visible where applicable.

Top young/prime RBs such as Bijan Robinson, Jahmyr Gibbs, De'Von Achane, and Kyren Williams are treated as prime-window players.

### WR

Older WRs with strong production can still remain high, but age/dropoff is visible:

- A.J. Brown and DJ Moore show `mild_decline`.
- Tyreek Hill and Davante Adams show `cliff_risk_window`.
- WR age + target/route decline interaction flags are present.

This matches the intended model behavior: do not blindly erase older productive WRs, but make the age risk inspectable.

### QB

Top QBs are mostly in prime window:

- Josh Allen, Jalen Hurts, Lamar Jackson, Patrick Mahomes, and Justin Herbert show visible age scores.
- Lamar Jackson is still prime-window by the current QB age curve.

Potential future model question: rushing-QB decline may deserve a separate earlier warning than pocket-passing QB decline. That is a formula/model policy question, not a data bug found in this audit.

### TE

Older TEs are being flagged:

- George Kittle, Mark Andrews, Evan Engram, Jonnu Smith, and Travis Kelce show age/dropoff warnings.
- TE late-prime/no-premium route-dependency flags are present.

This matches LVE logic: no TE premium means old TE value should depend heavily on route/target evidence, not generic TE scarcity.

## Review Flags

Only two rows were flagged for high age contribution share:

- MarShawn Lloyd
- Zonovan Knight

Both are fringe/low-info RB profiles outside the top asset range. The flag is a denominator effect: age is a large share of a weak total contribution stack, not a hidden boost creating a top rank. No patch was made.

## Patch Decision

No data, normalization, or receipt bug was found in the age/dropoff layer during this audit.

No scoring formulas were changed.

Rankings remain review-only.

## Remaining Model Risk

Age/dropoff is not the current trust blocker. The bigger remaining risks are still:

- role/usage truth gaps
- projection source quality
- cross-position balance
- named-player sanity fixtures
- receipt-backed model calibration

