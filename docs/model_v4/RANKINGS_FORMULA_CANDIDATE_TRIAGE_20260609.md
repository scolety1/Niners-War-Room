# Rankings Formula Candidate Triage - 2026-06-09

This report is proposal-only. It does not tune formulas, change weights, modify scores, or create roster recommendations.

## Answers

1. QB 1QB formula review is justified after source cleanup. The issue queue contains 28 QB format-sanity rows.
2. TE no-premium formula review is justified after source cleanup. The issue queue contains 31 TE format-sanity rows.
3. RB/WR balance review is justified only after human review confirms elite-player-too-low rows are true misses.
4. Veteran age/status confidence review is justified as a secondary candidate.
5. Young-player evidence sensitivity review is justified as a secondary candidate.
6. Remaining source/data blockers are limited to hidden kickers and source coverage warnings; non-kicker identity/team mismatch is cleared.
7. Likely formula candidates: QB 1QB spread/compression and TE no-premium ceiling/cap.
8. Possible model edge: market/league disagreement rows where private evidence supports the NWR placement.
9. First controlled experiment tomorrow: design a read-only QB/TE shadow comparison harness that reports candidate deltas without changing baseline scores.

## Candidate Hypotheses

- QB 1QB spread/compression may be over-rewarding replacement-level or aging QB profiles while depressing elite rushing/young QB profiles.
- TE no-premium ceiling/cap may over-reward elite TE scarcity relative to no-TE-premium format.
- RB/WR balance may need inspection only after QB/TE are isolated.
- Veteran no-team/FA confidence handling should remain capped and visible; do not convert status context into score changes without a controlled candidate.

## Required Evidence Before Implementation

- Human review worksheet annotations for top outliers.
- Component readbacks for suspicious rows.
- Shadow-only candidate deltas against the current full-board baseline.
- Sentinel and contamination checks rerun after any proposal.

## Current Issue Counts

| Issue bucket | Count |
| --- | ---: |
| elite_player_too_low | 10 |
| human_review_only | 11 |
| market_league_disagreement | 4 |
| qb_1qb_format_sanity | 28 |
| source_disclosure_gap | 16 |
| te_no_premium_format_sanity | 31 |
| veteran_age_confidence | 2 |
