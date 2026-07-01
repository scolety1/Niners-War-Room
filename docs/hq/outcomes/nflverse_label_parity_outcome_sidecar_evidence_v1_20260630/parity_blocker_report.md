# Parity Blocker Report

Verdict: `LABEL_PARITY_NOT_READY_FOR_PROMOTION`

## Blockers Before Any Label Truth Decision

1. Historical NFLVerse `player_stats` sidecar rows have not been built for the full label horizon.
2. Reproducible identity matching between existing labels and NFLVerse sidecar rows has not been audited.
3. Matched, unmatched-existing, and unmatched-NFLVerse counts are not available.
4. Scoring parity has not been proven against existing Outcome label definitions.
5. First-down scoring parity must be explicitly verified or caveated.
6. Season and position coverage gaps must be quantified.
7. Duplicate player-season and many-to-one identity collisions must be handled.
8. Right-censoring behavior must match existing Outcome horizon-label policy.
9. Missing player_stats rows must remain `Not enough information`.
10. Mismatch categories and acceptance thresholds are not defined.
11. Outcome V2 blocked fields remain blocked unless a separate calibration gate changes them.
12. Rookie Gate G remains blocked.

## Not Blockers for Review-Only Exploration

The current blockers do not prevent a future review-only sidecar evidence lane. They prevent label promotion, model training, source-truth promotion, and active probability output.

## Explicitly Blocked Uses Now

- Replacing existing labels with NFLVerse `player_stats`.
- Training from NFLVerse sidecar labels.
- Using labels as model input features.
- Creating current-player or rookie probabilities.
- Wiring sidecar data into Rankings or Player Compare.
- Treating missing sidecar data as zero, false, healthy, clean, or low risk.
