# Replay Blocker Report

## Blocking Decision

Replay is not approved for any source or feature in this builder packet.

## Counts

- Source rows with `replay_ready=true`: 0
- Feature rows with `replay_ready=true`: 0
- Feature rows with `experiment_ready=true`: 0
- Model/training/source-truth approved rows: 0

## Major Blockers

- No source has a full tracked point-in-time snapshot available.
- No source has a known extraction timestamp in the tracked manifest evidence.
- No source has a proven publication/as-of timestamp sufficient for historical replay.
- Current display artifacts are current-context summaries, not replay snapshots.
- Identity-safe display rows remain display/review-only; 13 player context rows remain gated.
- Availability denominator fields remain display-only; `games_missed_while_rostered` remains blocked by missingness policy.
- Injury/practice data cannot become health risk, clean health, durability, medical projection, or model input.
- Schedule data cannot become matchup recommendation, start/sit, playoff odds, or trade timing.
