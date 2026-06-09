# External Audit Prompt: Model v4 RotoWire Golden Candidate Layer

You are auditing a dynasty fantasy football model for a 10-team, 1QB,
non-PPR league with 0.4 points for rushing and receiving first downs.

The model is review-only. It must not be treated as live roster advice yet.

## Audit Goal

Determine whether the RotoWire-powered Model v4 candidate layer is directionally
sound, receipt-supported, honest about first-down estimates, and safe to
continue toward app promotion planning.

Do not assume the model is correct. Do not force rankings to match public
rankings. Identify unsupported rankings, source gaps, formula problems, and
acceptable model disagreements separately.

## Context

Important constraints:

- Active app rankings, My Team, War Board, and readiness gates are unchanged.
- RotoWire outputs are local licensed evidence.
- Raw licensed RotoWire exports are not included in this packet.
- Projections, ADP, rankings, market, and league rank must not drive private
  football value.
- Route, target, snap, alignment, and TE route evidence may be used only when it
  comes from licensed local RotoWire exports.
- RotoWire player-stat exports in the current packet do not expose direct
  rushing/receiving first-down fields.
- The current replacement/VORP layer estimates 2025 rushing/receiving first
  downs from source-safe 2022-2024 nflverse first-down history.
- Estimated first downs must be labeled `estimated_from_history`; they must not
  masquerade as direct evidence.
- Missing data cannot become zero evidence.
- Incoming rookies without sourced rookie/prospect or NFL evidence should have
  weak/review confidence.

## Files To Review

Start with:

- `docs/model_v4/ROTOWIRE_GOLDEN_BUILD_CHECKPOINT.md`
- `docs/model_v4/ROTOWIRE_FIRST_DOWN_AWARE_REPLACEMENT_PLAN.md`
- `docs/model_v4/ROTOWIRE_NEXT_PATCH_LIST.md`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.csv`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.csv`
- `local_exports/model_v4/rotowire_dynasty_candidate/latest/rotowire_dynasty_candidate_rows.csv`
- `local_exports/model_v4/rotowire_dynasty_candidate/latest/rotowire_dynasty_candidate_component_rows.csv`
- `local_exports/model_v4/rotowire_dynasty_candidate/latest/rotowire_dynasty_candidate_receipt_rows.csv`
- `local_exports/model_v4/rotowire_dynasty_candidate/latest/rotowire_dynasty_candidate_warning_rows.csv`
- `local_exports/model_v4/rotowire_vorp_review/latest/rotowire_vorp_review_rows.csv`
- `local_exports/model_v4/rotowire_replacement/latest/rotowire_replacement_baselines.csv`

## Specific Questions

1. Does the candidate layer honestly separate sourced evidence, proxy evidence,
   estimates, warnings, and unavailable sections?
2. Are projections, market, ADP, rankings, and league rank excluded from private
   football value?
3. Are QBs suppressed appropriately for 10-team 1QB, while preserving value for
   true rushing/VORP separators?
   - Specifically inspect Lamar Jackson: his dynasty value is heavily tied to
     rushing separation, but he is entering the age range where QB rushing
     advantage can decay. Should the model emit a sell-high/trade-review flag
     when market value still prices him as an elite separator?
4. Are TEs suppressed appropriately for no TE premium, while preserving value
   for true receiving engines?
5. Are age/dropoff caps working without unfairly erasing still-useful players?
6. Does De'Von Achane now look like an elite/core RB candidate rather than a
   legacy bubble asset?
7. Are the lower values for Malik Nabers, Brian Thomas Jr., and Luther Burden
   supported by receipts, or are they evidence/formula gaps?
8. Are older veterans such as Derrick Henry, Christian McCaffrey, Davante Adams,
   and Keenan Allen handled honestly?
9. Are incoming rookies such as Jeremiyah Love capped/reviewed appropriately
   until rookie/prospect data exists?
10. Is the first-down estimation layer honest and reasonable enough for
    review-only use, or does it create a formula/data blocker before app
    promotion planning?

## Output Requested

Produce a triage report with:

- verdict:
  - ready for app promotion planning
  - needs formula repair first
  - needs data/source repair first
  - needs receipt/confidence repair first
  - needs first-down estimation repair first
  - not enough evidence to audit
- issue table with:
  - severity
  - affected files
  - affected players or positions
  - evidence
  - likely cause
  - recommended next action
- suspicious rankings list
- accepted limitations list
- exact next patch list

Be blunt. Do not fake certainty. If a ranking is surprising but supported by
receipts, say so and explain why. If it is unsupported, identify the file,
field, component, or source gap causing it.
