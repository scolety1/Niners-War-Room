# LVE War Room Calibration Report

This report records the deterministic calibration fixtures used to keep the app aligned with the LVE decision model. It is not an outcome model yet. Historical rookie records currently provide draft-context provenance, while the scored fixtures test the formulas against known LVE decision traps.

## Calibration Fixtures

| scenario | expected behavior | current result |
|---|---|---|
| obvious keep | Elite veteran remains a strong keeper and does not become a cut candidate. | Passing |
| obvious cut | Weak veteran becomes a cut/shop candidate. | Passing |
| forced-release star | High-value top-five forced-release player is shopped before declaration instead of treated as a casual cut. | Passing |
| veteran vs rookie | Strong rookie asset beats a lower veteran on acquisition value. | Passing |
| pick vs player | Strong pick beats a bubble player through optionality. | Passing |
| QB in 1QB | Good pocket-only QB is structurally suppressed. | Passing |
| TE no premium | Low-capital TE is suppressed in no-premium scoring. | Passing |

## Historical Data Used

- `sample_data/historical_rookie_notes/offline_notes_four_seasons.csv`
- Seasons covered: 2022, 2023, 2024, 2025
- Records: 20 offline rookie-draft entries
- Current confidence: handwritten/offline note provenance
- Limitation: traded-pick ownership still requires manual review

## Sensitivity Result

The current calibration tests perturb one important veteran feature and one important rookie feature by +5 points. Neither produces a high-volatility output swing under the current formulas. That is the desired behavior: a single hand-entered feature should not radically reorder the board by itself.

## Current Formula Assessment

No formula change was made in Phase 24. The fixtures passed without needing to retune veteran, rookie, pick, or forced-release logic.

## App View

Implementation Phase G2 surfaces this report on the Historical Replay page in a
dedicated **Calibration Report** tab. The view shows:

- readiness areas for scenario fixtures, sensitivity, historical model-row
  coverage, and current-score isolation,
- replay verdict counts for the currently loaded historical comparison,
- deterministic scenario fixture rows,
- sensitivity rows,
- and the loaded historical rookie records.

The report is intentionally read-only. It may identify review areas, missing
as-of model rows, or historical misses, but it must not automatically retune
formulas or alter current War Board, Team, Trade Central, Draft Room, rookie, or
veteran scores.

Watch areas for future phases:

- Outcome labels are still thin. Historical records tell us who was drafted, not yet whether the model would have beaten the room.
- Veteran scoring remains placeholder-gated for the current live pack until complete normalized veteran inputs exist.
- Forced-release strategy is only as good as real model outputs plus league-rank accuracy.
- Sensitivity coverage is directional, not exhaustive; future work should perturb all live weights once the final veteran dataset is complete.
