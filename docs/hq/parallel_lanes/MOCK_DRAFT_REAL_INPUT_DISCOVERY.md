# Mock Draft Real Input Discovery

Discovery timestamp: 2026-06-19

## Scope

Read-only search for local Mock Draft candidate inputs. No real data was copied,
moved, edited, staged, or committed. No files were written to `data/` or
`local_exports/`. No simulations were run.

## Required Frozen Rookie Input

Expected path:

`local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`

Status: missing in this lane. This remains a YELLOW input-readiness gap.

## Candidate Paths Found

These files are candidates, templates, or fixtures only. Files outside this
Mock Draft lane remain read-only and must not be modified from this lane.

- `docs/model_v4/mock_draft_input_templates_20260617/behavior_only_adp_market_template.csv`
- `docs/model_v4/mock_draft_input_templates_20260617/dropped_veterans_template.csv`
- `docs/model_v4/mock_draft_input_templates_20260617/post_drop_rosters_template.csv`
- `templates/real_data_inputs/data_pack/fact_available_veterans.csv`
- `templates/real_data_inputs/data_pack/fact_rosters.csv`
- `templates/real_data_inputs/public_sources/player_market_inputs.csv`
- `sample_data/2026_pre_declaration/fact_rosters.csv`
- `tests/fixtures/mock_draft/input_schema_validator/*.csv`
- `tests/fixtures/mock_draft_inputs/*.csv`

Similar template/sample files also exist in sibling worktrees such as Rookie,
Outcome, Drop Decision, Deployment V2, Trading Lab, and Master. They are not
Mock Draft lane-owned real inputs and must remain read-only.

## Inputs Still Missing

- Frozen rookie mock draft input.
- Dropped/available veteran pool.
- Final pick order.
- NWR/my pick numbers.
- Current rosters/keepers.
- Team needs/opponent tendencies.
- NWR private value source.
- ADP/market behavior context.

## Notes

ADP/market context remains opponent behavior, availability, and likely pick
timing only. It must never become NWR private quality/value. Real files should
be configured later through a local-only manifest and validated before any
simulation work is considered.

## 2026-06-19 Refresh

Read-only discovery found 52 candidate CSV paths across `C:\NWR` and sibling
worktrees. The expected frozen rookie input path remains missing.

Candidate categories observed:

- Mock Draft template CSVs under
  `docs/model_v4/mock_draft_input_templates_20260617/`.
- Mock Draft fake fixtures under `tests/fixtures/mock_draft_inputs/`.
- Sample/template roster, veteran, and market CSVs under repository template
  folders and sibling worktrees.

Header-only examples observed:

- dropped-veterans template: player, position, source label, review flags,
  team context, and input status.
- post-drop roster template: team/manager/player/position/team/status fields.
- behavior-only ADP/market template: asset identity, source, market ADP,
  expected pick, sample size, and review flags.
- template market inputs include market value/rank fields and therefore remain
  behavior-only unless separately reviewed.

No real data was copied, moved, committed, or promoted. Files from sibling
lanes remain read-only references. No simulations ran. Real input readiness
remains YELLOW until user-approved local inputs are supplied.
