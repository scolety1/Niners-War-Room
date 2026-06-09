# Truth Set Lab v1 Intake 05: Young Player Prior

## Files

- Raw DOCX: `local_exports/truth_set_lab/v1/source_raw/young_player_data_collection.docx`
- Extracted text: `local_exports/truth_set_lab/v1/source_raw/young_player_data_collection.txt`
- Clean preview: `local_exports/truth_set_lab/v1/source_clean/young_player_prior.csv`
- Intake summary: `local_exports/truth_set_lab/v1/reports/young_player_prior_intake_summary.json`
- Intake flags: `local_exports/truth_set_lab/v1/reports/young_player_prior_intake_flags.csv`

## Intake Result

Status: `ready_for_review_not_model_use`

This report is the missing young-player / draft-capital / prospect-prior source. It is expected to cover young and early-career players, not all established veterans in the 40-player truth set.

## Coverage

- Truth-set rows expected: 40
- Expected young-prior rows: 23
- Extracted young-prior rows: 20
- Missing full truth-set players: 20
- Missing young-eligible players: 3
- Extra players: 0
- Malformed extraction rows: 0
- Rows missing source URL: 0
- Rows missing confidence value: 0

Missing young-eligible players:

- Ashton Jeanty
- Brock Bowers
- Jahmyr Gibbs

These gaps block complete young-bridge testing for the 40-player trial set, but they do not invalidate the 20 extracted rows.

## Extracted Fields

The clean preview includes:

- `player_name`
- `position`
- `nfl_team`
- `draft_year`
- `nfl_draft_round`
- `nfl_draft_pick`
- `draft_capital_score_if_defined`
- `college_team`
- `final_college_season`
- `college_dominator_or_share_if_available`
- `college_yards`
- `college_tds`
- `college_receptions_or_carries`
- `breakout_age_if_available`
- `athletic_testing_if_available`
- `rookie_year_nfl_production_summary`
- `source_name`
- `source_url`
- `source_date`
- `confidence_0_100`
- `notes`

The clean rows are marked `preview_only_not_scoring`.

## Flag Summary

| flag | count | impact |
|---|---:|---|
| `wikipedia_source` | 13 | Review before model use |
| `subjective_note_language` | 10 | Use structured fields only |
| `young_eligible_missing` | 3 | Blocks complete bridge test coverage |
| `approximate_value_marker` | 1 | Verify before model use |

## Safe Usage

Safe:

- Use as preview evidence for the young-player bridge layer.
- Use draft year, draft round, draft pick, college team, final college season, and source metadata for review.
- Use it to build a draft-capital-prior preview after deriving draft-capital score deterministically.
- Use it to identify missing young-prior coverage.

Unsafe:

- Do not promote these rows directly into scoring yet.
- Do not use descriptive notes as scoring evidence.
- Do not use Wikipedia-derived values without verification if they materially affect rankings.
- Do not treat missing players as low-prior players; they are source gaps.
- Do not score established veterans with draft capital.

## Recommended Next Step

Build a preview-only young-player bridge prior from the structured rows. The preview should derive draft-capital score from round/pick, keep college production and athletic testing as review context, and flag missing young-eligible players separately.
