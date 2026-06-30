# Final Rookie Entry Status Hygiene Recommendation

## Verdict

`YELLOW`

## Findings

- Historical rookie entry-status is not model-ready.
- Drafted-player-only Outcome work may proceed as explicitly drafted-only, review-only coverage.
- UDFA modeling may not proceed.
- Confirmed UDFA count is `0` because no source-approved confirmed-UDFA policy is
  available.

## Coverage Counts

- Total rows: `4653`
- Drafted: `1999`
- Confirmed UDFA: `0`
- Likely UDFA needs review: `2514`
- Free-agent rookie needs review: `0`
- Wrong universe: `138`
- Name collision: `2`
- Unknown: `0`
- Rows with blockers: `2898`

## Remaining Blockers

- A confirmed UDFA source policy is still missing.
- Player registry rookie-season evidence is review-only and cannot prove confirmed UDFA.
- Player-stats-only evidence mostly identifies pre-2000 veterans or identity conflicts, not clean
  2000-2024 rookie entrants.
- Missing draft capital must remain unknown and cannot become pick 0 or fake round 8.

## Recommended Next Branch

`work/rookie-confirmed-udfa-source-policy-v1-20260630`

That branch should identify an approved public UDFA/rookie-entry source and still avoid model
tuning, rankings, probabilities, and app wiring.
