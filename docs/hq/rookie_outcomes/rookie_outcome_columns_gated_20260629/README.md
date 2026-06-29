# Rookie Outcome Columns Gated Lane - 2026-06-29

## Gate Results

- Gate A - CFBD identity human approval: `BLOCKED_NEEDS_CFBD_APPROVAL`
- Gates B-G: not run because Gate A is blocked.

## Where This Lane Stopped

The lane stopped at Gate A and created the required CFBD rookie identity
human approval packet.

## Active Blockers

- No tracked human-approved CFBD identity artifact exists.
- CFBD identity links remain review-only and blocked for model/training use.
- Draft capital, label, feature, model, display, and Rankings gates were not run.

## Artifacts Created

- `00_GATE_A_CFBD_APPROVAL_BLOCKER.md`
- `cfbd_rookie_identity_human_approval_packet.csv`

## Counts

- Approval packet rows: 213
- CFBD identity rows approved for model use: 0
- CFBD rows with recruiting context: 0

## Rankings / Active Columns

- Rankings was not touched.
- Active rookie outcome columns were not added.
- Rookie probabilities were not generated.

## Scoring Status

No scoring artifact was built because the lane stopped before historical
label/model gates.
Exact vs approximate scoring remains blocked for future work.

## Human Review Checklist

1. Review every row in `cfbd_rookie_identity_human_approval_packet.csv`.
2. Choose one valid human decision: `APPROVE_REVIEW_ONLY`, `REJECT`,
   `DEFER`, or `KEEP_BLOCKED`.
3. Add reviewer notes for ambiguous or possible candidates.
4. Keep `model_use_allowed=false` and `training_allowed=false` until a
   later explicit gate.

## Recommended Next Lane

`CFBD Rookie Identity Human Approval Packet V1`
