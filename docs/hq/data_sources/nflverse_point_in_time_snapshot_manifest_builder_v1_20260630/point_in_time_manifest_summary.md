# Point-in-Time Manifest Summary

Verdict: `YELLOW_POINT_IN_TIME_MANIFEST_BUILT_REPLAY_NOT_APPROVED`

## Scope

This packet builds review-only point-in-time/as-of manifest evidence from tracked repository artifacts. It does not read raw shared data, approve replay, approve experiments, train models, create probabilities, or wire app behavior.

## Manifest Counts

- Source snapshot manifest rows: 14
- Feature replay manifest rows: 14
- Sources with any timestamp/date/week evidence: 12
- Sources with partial as-of evidence: 1
- Sources with full point-in-time snapshot available: 0
- Replay-ready feature rows: 0
- Experiment-ready feature rows: 0
- Model/training/source-truth allowed rows: 0

## Tracked Context

- Player context display rows: 294
- Identity-safe display rows: 281
- Gated player context rows: 13
- Availability denominator rows: 588
- Safe availability denominator player-season rows: 437
- Gated availability denominator rows: 151
- Bound review-only identity rows from binding packet: 41

## Finding

The tracked artifacts provide useful display/review context and partial date/week/source-as-of clues, but they still do not provide complete point-in-time snapshot proof. Every source and feature remains blocked for replay and experiment until a later HQ gate supplies extraction timestamps, publication/as-of timestamps, prediction anchors, identity exclusions, missingness policy, and leakage diagnostics.
