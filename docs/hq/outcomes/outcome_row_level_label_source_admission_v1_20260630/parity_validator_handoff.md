# Parity Validator Handoff

## Handoff status

The previous parity validator blocker is unblocked for Veteran Outcome V2 row-level label-source availability.

The compact artifact now provides row-level labels with:

- player identity (`player_id`)
- player name
- position
- season or anchor season
- label family
- label name
- label value
- hit status
- window completeness
- censoring status
- source SHA
- review/model/training/source-truth flags

## Artifact for next lane

`docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/compact_outcome_row_level_label_source.csv`

Rows: `119,040`

## Remaining caveats

- `nwr_player_id` is `Not enough information` for these historical label rows unless a later approved historical identity bridge fills it.
- `label_truth_allowed=false`; the validator may use these rows for review/parity comparison only.
- Rookie labels remain separate and Gate G is not approved here.
- No app display or probability changes are authorized by this packet.
