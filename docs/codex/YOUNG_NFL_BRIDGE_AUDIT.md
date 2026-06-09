# Young NFL Bridge Audit

Date: 2026-05-12

Active pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Audit artifacts:

- `local_exports/young_nfl_bridge_audit.csv`
- `local_exports/young_nfl_bridge_flags.csv`
- `local_exports/young_nfl_bridge_summary.csv`
- `local_exports/young_nfl_bridge_selected_players_audit.csv`

## Scope

This pass audits whether year-one, year-two, and year-three NFL players are being handled as bridge assets instead of pure rookies or pure veterans.

The audit checks draft-capital prior, decay weight, NFL evidence weight, final bridge contribution, lifecycle assignment, and whether established veterans accidentally receive draft-capital prior.

## Supported Bug Patch

The bridge layer had one supported bug: generated `young_nfl_bridge_weight` metadata was being treated like an explicit/manual override. That prevented the model from recalculating decay from NFL evidence for some year-two and year-three players.

Patch made:

- Generated bridge weights are now recalculated from current NFL evidence.
- Only rows with `young_nfl_bridge_weight_source` set to `manual`, `manual_override`, or `approved_override` can force a bridge weight.
- Established veterans ignore leaked generated bridge weights and remain at bridge weight `0.0`.

## Current Bridge Behavior

The patch reduced bridge contribution for players with real NFL evidence:

- Bijan Robinson: year-three bridge weight about `0.047`; bridge contribution about `0.65`.
- Jahmyr Gibbs: year-three bridge weight about `0.047`; bridge contribution about `0.50`.
- Brian Thomas: year-two bridge weight about `0.124`; bridge contribution about `1.59`.
- Malik Nabers: year-two bridge weight about `0.124`; bridge contribution about `2.23`.
- JSN: year-three bridge weight about `0.047`; bridge contribution about `1.36`.
- De'Von Achane: year-three bridge weight about `0.047`; bridge contribution about `0.15`.

That is the intended shape: early draft/prospect priors are still visible, but real NFL evidence mostly owns the score once a player has useful data.

## Review Flags That Remain

The 2025 class remains heavily review-only because the active import does not yet contain enough NFL production/role evidence:

- Luther Burden
- Jayden Higgins
- Kaleb Johnson
- incoming 2025 rookie/free-agent pool rows

Those rows correctly show `missing_nfl_evidence` and, for higher-capital players, `bridge_contribution_too_dominant`. This is not a formula bug; it is the model admitting the current score is mostly prior and uncertainty.

## Established Veteran Check

The lifecycle audit found `0` established veterans with scored draft-capital prior after the patch. That is the required safety behavior.

## Decision Status

Keep rankings review-only.

The bridge layer now behaves more correctly, but young players with missing NFL evidence still need better production/role imports or explicit review before they can be used for money decisions.
