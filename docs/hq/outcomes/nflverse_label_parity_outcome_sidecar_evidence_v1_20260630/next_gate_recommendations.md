# Next Gate Recommendations

## Safe Now

- Keep the current packet as review-only policy evidence.
- Use the matrix to scope a future sidecar builder.
- Preserve current Outcome V2 and Rookie Outcome non-activation posture.

## Recommended Next Lane

Create a `NFLVerse Player Stats Historical Sidecar Builder` lane.

Required outputs:

- historical player_stats sidecar rows by player, season, and position;
- source manifest;
- schema manifest;
- identity join audit;
- row-count and coverage report;
- no model/training/source-truth approvals.

## Follow-On Label Parity Lane

After the sidecar builder exists, run a label parity gate that reports:

- exact label definitions;
- scoring mode and first-down parity;
- label-to-sidecar identity matches;
- unmatched existing labels;
- unmatched NFLVerse rows;
- duplicate/collision handling;
- season and position coverage;
- right-censoring behavior;
- mismatch categories;
- acceptance thresholds;
- explicit keep-blocked/promote-review-only decisions.

## Safe Only After Model Gate

- Any model feature use of NFLVerse `player_stats`.
- Any training use.
- Any active current-player probabilities.
- Any active rookie probabilities.
- Any Rankings or Player Compare probability display not already approved elsewhere.

## Blocked

- Label truth promotion from this packet.
- Gate G approval from this packet.
- UDFA modeling.
- CFBD model/training input.
- Missing data as zero, false, healthy, clean, or low risk.
- Market, ADP, DynastyProcess, vendor, or Gmail inputs.
