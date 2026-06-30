# Label Parity Requirements

Verdict: `YELLOW_LABEL_PARITY_REQUIREMENTS_DEFINED_NO_LABEL_PROMOTION`

This packet does not promote labels, player_stats sidecars, training truth, or source truth. It defines the evidence required before any future label or sidecar family can be considered for stronger use.

## Label Families Covered

- `player_stats sidecar`
- `Outcome V2 labels`
- `Rookie Outcome labels`

## Current Policy

Outcome V2 historical label evidence remains review-only. Rookie drafted-only label work remains review-only. NFLVerse `player_stats` can support a future public sidecar comparison lane, but it is not label truth, model input, training truth, or source truth now.

Missing labels remain `Not enough information`. Incomplete windows remain right-censored and are not failures.

## Required Parity Evidence

A future label parity lane must provide:

- source artifact manifest;
- label specification and scoring mode;
- player identity bridge;
- season/year coverage;
- position coverage;
- anchor/horizon definitions;
- duplicate and collision handling;
- right-censoring logic;
- comparison against existing Outcome V2 labels;
- mismatch categorization;
- acceptance thresholds;
- blocked-field table;
- explicit non-activation statement.

## Sidecar Rules

`player_stats` sidecars may only compare against approved label specs. They may not become:

- training truth;
- source truth;
- model input;
- rank input;
- hidden sort;
- current probability activation;
- Rookie Gate G release evidence by themselves.

## Outcome V2 Requirements

Any future Outcome V2 current-player use must separately pass:

- current identity bridge gate;
- feature freshness/as-of gate;
- blocked-source scan;
- missingness policy gate;
- validation/calibration gate;
- display or activation approval gate.

Prior 2000-2024 review-only historical evidence does not activate current-player probabilities.

## Rookie Requirements

Any future Rookie Outcome label use must separately pass:

- drafted-only admission gate or later approved UDFA source gate;
- label-source partition gate;
- historical replay/leakage gate;
- label parity gate against Outcome V2 label definitions;
- Gate E/F/G posture review;
- explicit approval before any model/training/source-truth use.

No active rookie probabilities are approved by this packet.
