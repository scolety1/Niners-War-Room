# Gate C Historical Label Decision - 2026-06-30

## Verdict

`PARTIAL_HISTORICAL_ROOKIE_LABELS`

Partial historical rookie labels were built for drafted QB/RB/WR/TE rows
that link through the approved review-only GSIS/player_stats bridge to
Outcome V2 exact first-down target labels.

## What Is Partial

- Bridge rows considered: 1025
- Label rows built: 919
- Blocked bridge rows: 106
- UDFA/free-agent rookies are not included.
- Missing GSIS and unlinked rows remain blocked.
- Recent incomplete windows remain right-censored.

## Gate D

Gate D can run next as a review-only partial drafted-player feature policy
gate. It must not promote these labels to model/training/source truth.
