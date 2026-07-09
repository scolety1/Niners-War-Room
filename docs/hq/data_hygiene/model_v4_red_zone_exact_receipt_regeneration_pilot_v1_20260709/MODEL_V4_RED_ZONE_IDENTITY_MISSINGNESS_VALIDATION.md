# Model v4 Red Zone Identity / Missingness Validation

Result: `PASS_PARTIAL_WITH_IDENTITY_AND_MISSINGNESS_CAVEATS`

- Source rows without GSIS player ID excluded from player-season receipts: `1077`
- Identity flags: `IDENTITY_LIMITED_GSIS_PRESENT_BUT_NO_REVIEW_MART_POSITION_NAME=159, PARTIAL_GSIS_TO_REVIEW_MART_LATEST_IDENTITY=605, PASS_GSIS_TO_REVIEW_MART_IDENTITY=542`
- Position coverage: `QB=228, RB=346, TE=198, UNKNOWN=159, WR=375`

The source sidecar contains Sleeper and GSIS IDs but does not contain player name or position. Names and positions are added only when the review-only formula data mart has a matching GSIS identity. Rows without a safe position/name join are preserved with `UNKNOWN` position and an identity-limited flag.

Sparse missing Sleeper keys are unknown/not enough information, not zero. No synthetic zero receipt rows were generated.
