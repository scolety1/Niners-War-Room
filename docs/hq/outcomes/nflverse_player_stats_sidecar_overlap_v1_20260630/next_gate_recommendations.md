# Next Gate Recommendations

## Safe Now

- Keep this packet as review-only count-level overlap evidence.
- Use the matrix to scope the next row-level sidecar builder.
- Keep all label truth, model, training, source-truth, probability, and app approvals false.

## Next Required Lane

Create a `NFLVerse Player Stats Historical Sidecar Builder V1` lane.

Required evidence:

- tracked or generated review-only sidecar rows by `player_id` or `gsis_id`, `season`, `week`, `position`, and team;
- source manifest and schema manifest;
- row counts by season and position;
- identity bridge audit;
- no app integration;
- no model/training/source-truth activation.

## Follow-On Parity Gate

After row-level sidecar rows exist, run a `NFLVerse Label Parity Gate` that computes:

- matched players;
- unmatched existing labels;
- unmatched NFLVerse rows;
- identity match rate;
- scoring parity;
- first-down scoring status;
- censoring parity;
- mismatch categories;
- acceptance thresholds.

## Still Blocked

- Label truth promotion.
- Active current-player probabilities.
- Active rookie probabilities.
- Rookie Gate G.
- Model input use.
- Training use.
- Source-truth use.
- Missing data as zero, false, healthy, clean, or low risk.
