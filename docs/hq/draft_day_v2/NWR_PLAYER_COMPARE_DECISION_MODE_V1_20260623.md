# NWR Player Compare Decision Mode V1 - 2026-06-23

## Verdict

GREEN.

Player Compare now starts with a decision-first summary for two-player comparisons, while still allowing optional 3- or 4-player context checks. The feature is review-only and does not mutate ranks, tiers, model values, frozen baseline data, or source-truth artifacts.

## What Decision Mode Does

- Adds explicit `Player A` and `Player B` selectors.
- Keeps optional extra players for 3- or 4-player comparisons.
- Shows a top `Decision Summary` before detailed data.
- Provides:
  - lean
  - confidence
  - best use case
  - data quality
  - main reasons
  - red flags / checks
  - compact comparison rows
- Keeps detailed context in tabs and expanders below the summary.

## Decision Logic

Primary decision signals are NWR-controlled display fields:

1. `dynasty_asset_rank`
2. `cross_asset_candidate_rank`
3. `final_board_rank` as frozen baseline rank/checkpoint context
4. tier/band fields
5. age context
6. position/outcome/caveat context
7. injury/per-game warnings when available

Close rank gaps return `Close / depends on roster` rather than forcing a fake winner. Missing rank context returns `Not enough information` with low confidence.

## Primary Data

The decision helper treats NWR rank/tier/outcome/caveat fields as the primary decision context. It does not edit or overwrite any rank, tier, source file, or model artifact.

## Display-Only Data

Market/ADP/DynastyProcess context remains display-only sanity context. It can appear in the summary as a timing or sanity note, but it cannot create the recommendation by itself.

The summary displays:

`Market/ADP context is display-only sanity context and does not decide the lean.`

## Missing-Data Behavior

Missing values show exactly:

`Not enough information`

Unsupported Outcome context is not treated as a bad outcome. It is a confidence/data-quality caveat only.

## Tests And Checks

- Clear rank/tier edge creates a lean.
- Close ranks create `Close / depends on roster`.
- Missing rank data creates `Not enough information` or low confidence.
- Market data alone cannot create a recommendation.
- Injury/per-game warnings appear as red flags when available.
- Display-only market label appears when market context appears.
- Unsupported Outcome is not treated as bad Outcome.
- No rank/model/source-truth mutation.

## Browser Smoke

Browser smoke covered:

- `/player-compare`
- `/rankings`
- `/trading-lab`
- `/live-draft-room`
- `/cheat-sheets`
- `/mock-draft`
- `/post-draft-mode`

Player Compare proof targets:

- `Jameson Williams` vs `Brian Thomas`
- `Zay Flowers` vs `Chris Olave`
- page opens with Decision Summary first
- confidence, reasons, red flags, and display-only market note visible
- detailed tabs remain available below the summary

## Known Limitations

- The decision summary is a review aid, not a source-truth rank.
- Market context is not a trade calculator and not a model input.
- Injury/per-game context remains limited by the YELLOW injury audit coverage.
- Roster-fit logic is intentionally conservative until richer roster/needs data is approved.
