# Rookie Gate E/F/G Requirements

Verdict: `YELLOW_ROOKIE_GATE_REQUIREMENTS_LOCKED_NO_GATE_G`

This packet does not approve rookie model training, active rookie probabilities, app-facing rookie columns, Rankings wiring, Gate G, or source-truth promotion.

## Gate E

Gate E remains review/R&D feasibility only.

Current limits preserved:

- drafted-player-only label population where separately approved;
- no current-player rookie probabilities;
- no production model promotion;
- no training approval;
- no tuning approval;
- no feature promotion;
- no source-truth promotion.

Any future Gate E revisit must first pass the feature-family gates in `nflverse_feature_gate_matrix.csv`.

## Gate F

Gate F remains review-only or display-only coverage where already explicitly approved. It cannot become model-ready from this packet.

Required limits:

- missing fields remain `Not enough information`;
- partial coverage must remain visible;
- display rows cannot imply probability approval;
- no Rankings integration;
- no hidden sort;
- no app-facing rookie probability columns;
- no current fake T12/T24/T36 outputs.

## Gate G

Gate G remains blocked.

Gate G cannot reopen until a separate user-approved release lane proves:

- identity coverage;
- source policy;
- historical replay;
- label parity;
- missingness;
- leakage;
- validation/calibration;
- UI risk;
- protected artifact boundaries;
- explicit model/training/source-truth approvals.

## UDFA Boundary

UDFA modeling remains blocked. Draft absence, roster appearance, weekly roster appearance, player_stats appearance, snap appearance, depth chart appearance, injury context, or schedule context cannot confirm UDFA status.

Confirmed UDFA source evidence remains unavailable for model/training use in the currently inspected packets.

## CFBD Boundary

CFBD model/training input remains blocked. CFBD identity joins require stable IDs, school timelines, transfer handling, conflict handling, and explicit human review before any stronger use can be considered.

Current approved historical CFBD model/training join count remains `0`.
