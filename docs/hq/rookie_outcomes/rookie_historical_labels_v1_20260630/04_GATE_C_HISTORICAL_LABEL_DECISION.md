# Gate C Historical Label Decision - 2026-06-30

## Verdict

`BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE`

The NFL outcome target source is review-only green, and the label spec is
defined. A historical rookie label artifact was not built because the lane
does not have an approved historical rookie draft-class and GSIS outcome ID
bridge.

## Row Counts

- Bridge rows audited: 157
- Rows linked to Outcome V2 labels: 0
- Rows with draft/rookie class year: 54
- Historical rookie label rows built: 0

## Source-Policy Status

- Target source gate: `GREEN_REVIEW_ONLY_NFL_OUTCOME_TARGET_SOURCE`
- Scoring mode available: `exact_verified_first_downs`
- Exact vs approximate scoring: exact verified first downs available for Outcome V2 target source.

## Coverage

- Outcome target seasons: 2012-2024
- Outcome target rows: 7440
- Complete 5Y rows: 1064
- Class/year coverage for rookie labels: blocked; no approved historical draft-class bridge.
- Position coverage for target source: QB/RB/WR/TE available in Outcome V2 labels.

## Draft Capital / CFBD Limitations

- Gate B draft capital is partial and current 2026 review-only context.
- CFBD identities remain review-only and are not model/training inputs.
- CFBD does not supply NFL outcome truth.

## Gate D

Gate D cannot run next. Required next blocker to clear: build an approved
historical rookie draft-class and NFL outcome ID bridge.
