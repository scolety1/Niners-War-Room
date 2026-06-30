# Next Parallel Evidence Lanes

Verdict: `YELLOW_NEXT_LANES_DEFINED_NOT_RUN`

These are safe next lanes to run later. This packet does not run them, generate artifacts for them, train models, tune models, score players, or activate app behavior.

## 1. Historical Replay / Leakage Evidence Lane

Purpose:

Define as-of-safe historical replay tests for roster status, weekly roster status, injury/practice status, schedule context, depth chart role, snap recency/sample, last active season/week, draft capital, combine, and availability denominator fields.

Required outputs:

- feature-window matrix;
- prediction-anchor contract;
- source snapshot manifest;
- identity pass/fail report;
- leakage diagnostics;
- missingness diagnostics;
- blocked-field table;
- no-activation guardrail report.

Stop condition:

If a feature cannot prove availability at the prediction anchor, it remains display/review-only or blocked.

## 2. Label Parity / Outcome Sidecar Evidence Lane

Purpose:

Compare NFLVerse `player_stats` sidecars against existing Outcome V2 and Rookie Outcome label definitions without promoting the sidecar to label truth.

Required outputs:

- label spec;
- parity matrix;
- mismatch taxonomy;
- censoring report;
- source-policy report;
- label-source partition table;
- no-training/no-source-truth guardrail report.

Stop condition:

If sidecar parity cannot be proven, the sidecar remains review-only and cannot become model input, training truth, label truth, or source truth.

## 3. Availability Denominator Missingness Evidence Lane

Purpose:

Define denominator semantics and missingness behavior for availability fields before any model or label interaction is considered.

Required outputs:

- denominator definition;
- rostered-game rule;
- bye/cancellation handling;
- active/inactive source hierarchy;
- missingness matrix;
- games-missed block audit;
- medical projection guardrail report.

Stop condition:

If missing availability can be confused with healthy, clean, played, missed, or no-risk, the lane remains blocked.

## 4. Rookie Drafted-Only Feature Gate Evidence Lane

Purpose:

Evaluate drafted-only Rookie Outcome feature candidates without UDFA modeling, CFBD training input, Gate G, or app wiring.

Required outputs:

- drafted-only admission matrix;
- draft capital and combine source policy;
- rookie historical replay report;
- label parity handoff;
- CFBD and UDFA blocker report;
- Gate E/F/G status update;
- no-probability/no-Rankings guardrail report.

Stop condition:

If a candidate requires UDFA source truth, CFBD model/training joins, or active rookie probabilities, it remains blocked.
