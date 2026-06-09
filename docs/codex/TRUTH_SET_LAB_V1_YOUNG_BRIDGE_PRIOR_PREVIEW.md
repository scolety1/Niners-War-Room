# Truth Set Lab v1 Young Bridge Prior Preview

This artifact converts the sixth Truth Set Lab report into preview-only young-player bridge-prior evidence.
It does not change live model scores, rankings, gates, or receipts used by the app.

## Outputs

- Preview CSV: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\young_bridge_prior_preview.csv`
- Receipt-style summary: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\young_bridge_prior_receipts.csv`
- Flags: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\young_bridge_prior_preview_flags.csv`

## Summary

- Rows: 23
- Source rows: 23
- Missing young bridge rows: 0
- Scored bridge-prior rows: 20
- Established/not-scored rows: 3
- Incoming rookies: 0
- Year-one bridge rows: 5
- Year-two bridge rows: 7
- Year-three bridge rows: 8

## Gap-Fill Controls

The prior missing controls are now present:

- Jahmyr Gibbs: 2023 round 1 pick 12, Detroit Lions, NFL.com source
- Ashton Jeanty: 2025 round 1 pick 6, Las Vegas Raiders, NFL.com source
- Brock Bowers: 2024 round 1 pick 13, Las Vegas Raiders, NFL.com source

Only factual draft-capital fields were added for these rows. College production and athletic testing remain blank/review-only instead of being invented.

## Guardrails

- Draft capital is blank for established veterans.
- Missing report rows stay flagged instead of receiving invented values.
- Subjective prospect notes are display/context only.
- College production and athletic testing are contextual strings, not normalized scores.
- Model usage status remains `preview_only_not_scoring`.
