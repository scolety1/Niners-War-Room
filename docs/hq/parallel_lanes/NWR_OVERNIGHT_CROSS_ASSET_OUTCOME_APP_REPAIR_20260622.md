# NWR Overnight Cross-Asset + Outcome + Draft App Repair - 2026-06-22

## Final Verdict

YELLOW-GREEN.

The app is morning-usable. The remaining YELLOW caveats are data-policy caveats, not app-breaking issues:

- Cross-asset candidate value is review-only and does not replace Final Board Rank or Dynasty Rank.
- ADP is from a YELLOW display-only Sleeper context and is converted into available-pool price context; it is not a model/rank input.
- Outcome support remains partial, and unsupported applicable heads still show `Not enough information`.
- No approved 2026/2027/5-year horizon Outcome artifact exists, so horizon probabilities were not implemented.

## Guardrail Statement

No latest_candidate or latest_approved file was created or updated. The pinned snapshot and frozen Final Draft Board V1 were not mutated. No approved Dynasty Rank or Final Board Rank values were overwritten. No vendor CSVs, raw prediction dumps, or `C:\NWR_SHARED_DATA` contents were tracked.

## Morning Usability

GREEN for practical morning app use:

- Live Draft Room now defaults to a visible `Candidate Best Available` review mode.
- Final Board Rank remains visible beside Candidate Rank.
- Pick assignment, auto-advance, undo, and remove/edit still work.
- Dynasty Rankings defaults to no kickers and hides source-coverage/final-board/debug clutter.
- Outcome display is position-aware.
- Player Compare includes cross-asset candidate metrics and a position-aware Outcome block.
- Mock Draft and Trading Lab smoke-tested without route errors.

## Formula Used

The app uses a repo-safe candidate artifact:

`docs/hq/parallel_lanes/cross_asset_formula_app_repair_20260622/cross_asset_candidate_player_board.csv`

The candidate formula came from the cross-asset lane commit `e9af53723d419325b4c9e2ff99e374880a512ca0`.

Core output fields:

- `cross_asset_candidate_value`
- `cross_asset_candidate_rank`
- `candidate_value_band`
- `confidence_band`
- `uncertainty_reasons`
- `candidate_vs_frozen_note` represented in the app as visible candidate rank/value beside Final Board Rank
- `available_pool_adp_rank`
- `available_pool_adp_range`
- `current_pick_value`

The app labels these fields as review-only candidate context.

## Rookie / Veteran Normalization

The repair does not compare raw frozen rookie score directly to raw veteran dropped-pool value.

Instead:

- Veterans/current NFL players use the internal full-dynasty score/rank/value where available as the long-term anchor.
- Rookies/prospects use a conservative rookie rank/tier/score crosswalk onto a 0-100 review scale.
- Uncertainty penalties are applied for manual review flags, needs-data style caveats, unknown/weak role evidence, mixed score basis, missing Outcome support, and caveat-heavy rows.

This fixes the misleading UI behavior where rookie scores near 90 and veteran values near 50 looked directly comparable.

## ADP / Startup Adjustment

Startup ADP is not treated as literal draft slot.

Repair:

- Raw ADP remains display-only.
- The 66-player available/frozen pool is sorted by ADP to create `available_pool_adp_rank`.
- `available_pool_adp_range` maps the available-pool ADP rank into draft-context labels:
  - Early 1st equivalent
  - Mid 1st equivalent
  - Late 1st equivalent
  - Early 2nd equivalent
  - Mid/Late 2nd equivalent
  - Depth / later
  - Not enough information
- Live Draft Room recomputes `Current Pick Value` from current pick, available-pool ADP rank, candidate rank, and confidence.

ADP/range context is visibly labeled display-only and does not drive NWR rank.

## Outcome Columns

Current approved Outcome heads remain:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

Display behavior:

- Position-applicable mode is the default.
- Wrong-position outcomes are hidden by default.
- In all-outcome/advanced mode, wrong-position outcomes render as `N/A`.
- Same-position missing support renders exactly as `Not enough information`.
- Outcome columns remain display-only and do not drive default sort.
- Live Draft Room does not show Outcome heads by default.
- Player Compare shows a position-aware Outcome block.

Future horizon note:

- The desired future taxonomy should be calendar-year based, such as `2026 T12 probability` and `2027 T12 probability`.
- No approved horizon artifact exists yet; no horizon probabilities were fabricated or implemented.

## Biggest Candidate Moves Up Vs Frozen Board

| Player | Pos | Frozen Rank | Candidate Rank | Candidate Value | Confidence |
|---|---:|---:|---:|---:|---|
| Zay Flowers | WR | 31 | 2 | 56.53 | Medium-high |
| Chris Olave | WR | 34 | 6 | 54.07 | Medium-high |
| Drake Maye | QB | 40 | 10 | 49.35 | Low |
| Jameson Williams | WR | 42 | 11 | 48.49 | Medium-high |
| Alec Pierce | WR | 47 | 12 | 47.95 | Medium-high |
| Jaylen Warren | RB | 54 | 23 | 34.20 | Medium-high |

These are review-only signals, not rank overwrites.

## Biggest Candidate Moves Down Vs Frozen Board

| Player | Pos | Frozen Rank | Candidate Rank | Candidate Value | Confidence |
|---|---:|---:|---:|---:|---|
| Barion Brown | WR | 20 | 38 | 28.75 | Very low |
| Kentrel Bullock | RB | 25 | 40 | 28.00 | Very low |
| Lewis Bond | WR | 22 | 35 | 29.60 | Low |
| Antonio Williams | WR | 10 | 18 | 38.00 | Very low |
| Chris Bell | WR | 8 | 13 | 47.25 | Low |

These rows need human judgment, especially where rookie role evidence is weak.

## Human Decision Players

Highest-priority manual review:

- Drake Maye: candidate rank improves substantially, but 10-team 1QB format suppresses QB replacement value.
- Zay Flowers / Chris Olave / Jameson Williams: no longer buried in the candidate view; draft only if room price fits.
- Keenan Allen / Darren Waller: still constrained by age/role/manual-review caveats.
- Low-confidence rookies with manual review flags should not be auto-promoted by the candidate view.

## Live Draft UI Changes

- Added `View / sort mode`:
  - Candidate Best Available
  - Frozen Board Rank
  - ADP / Price Context
- Default mode is Candidate Best Available.
- Main table prioritizes:
  - Candidate Rank
  - Final Board Rank
  - Player
  - Pos
  - NFL Team
  - Age
  - Position Rank
  - Candidate Band
  - Candidate Value
  - Confidence
  - ADP
  - Available-Pool ADP Range
  - Current Pick Value
  - Key Caveat / Review Flag
- Drafted players remain hidden by default.
- Draft Status / Assigned Pick / Board Availability / Draft Action / raw mixed-basis visible score / source coverage are not in the default table.

Browser proof:

- `/live-draft-room` showed 66 rows, Candidate Best Available, Candidate Rank, Final Board Rank, and review-only/display-only labels.
- Assigning 1.01 moved current pick to 1.02 and changed available count from 66 to 65.
- Undo restored current pick to 1.01 and available count to 66.

## Dynasty Rankings UI Changes

- No kickers by default.
- Source Coverage, Asset Type, Final Board Rank, Board Availability, and Draft Action are not foregrounded in the default Full Dynasty Rankings view.
- Added filters for:
  - position
  - tier/band
  - confidence
  - manual review
  - Outcome availability
  - age range
  - team
  - search
- Added visible caption explaining Candidate Rank / Candidate Value are review-only and do not replace Dynasty Rank or Final Board Rank.
- Position-aware Outcome controls remain visible.

Browser proof:

- `/rankings` rendered without route/app errors.
- Default position filter excluded K and showed QB/RB/TE/WR.
- Full dynasty rows badge showed 240.
- Frozen board rows badge showed 66.
- Outcome mode showed `Position-applicable only`.
- Source Coverage was not visible in the default top view.

## Player Compare Changes

- Added `Cross-Asset Candidate Comparison` block:
  - Candidate Rank
  - Final Board Rank
  - Candidate Value
  - Candidate Band
  - Confidence
  - ADP/range display-only context
  - Key caveat/review flag
- Added position-aware Outcome block in the prior repair.

Browser smoke:

- `/player-compare` rendered without route/app errors and exposed player selection.
- Browser text-entry into Streamlit multiselect hit an in-app browser virtual clipboard limitation during proof, but the route rendered and the code path is covered by service tests and direct page smoke.

## Sanity Checks

- Zay Flowers, Chris Olave, Jameson Williams, and Drake Maye are no longer buried in Candidate Best Available.
- Top rookies remain visible; Jeremiyah Love remains candidate rank 1.
- Low-confidence rookies remain flagged with uncertainty.
- QB is not blindly promoted: Drake Maye improves but carries low confidence and manual review.
- Missing Outcome is not treated as zero.
- Wrong-position Outcome is not treated as missing information.

## Validation

Passed:

- `python -m pytest tests/test_draft_day_app_v1_service.py tests/test_draft_day_workflow_service.py`
  - 30 passed.
- `python -m ruff check app/pages/20_final_board_v1.py app/pages/22_player_compare_v1.py app/components/draft_workflow.py src/services/draft_day_app_v1_service.py src/services/draft_day_workflow_service.py tests/test_draft_day_app_v1_service.py tests/test_draft_day_workflow_service.py`
- `git diff --check`
- Streamlit launched at `http://127.0.0.1:8501/rankings`.
- Browser smoke:
  - `/live-draft-room`
  - `/rankings`
  - `/player-compare`
  - `/mock-draft`
  - `/trading-lab`
  - `/settings`

Guardrails:

- Frozen board remains 66 rows.
- Pinned hash unchanged:
  `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- No `C:\NWR_SHARED_DATA` files tracked.
- No raw vendor CSVs or prediction dumps added.
- latest_candidate/latest_approved paths remain absent/untouched in this repo.

## Remaining Caveats

- Candidate Best Available is review-only.
- ADP source is still YELLOW display-only context.
- No expanded Sleeper all-free-agent pool was added; app still uses the frozen 66-row board for live draft workflow.
- Full dynasty top players outside the frozen/candidate board may have no candidate rank/value, by design.
- Player Compare multiselect selection could not be fully browser-proven due the in-app browser virtual clipboard issue, though page smoke and service validation passed.
