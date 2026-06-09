# Truth Set Lab v3 Decision Recommendation

Status: no model logic changed. This is a gate/recommendation report only.

## Recommendation

Roster decisions are ready only on the current active model gate. Truth Set Lab v3 remains review-only and should not be promoted until its preview artifacts can pass active-schema source coverage, identity, and outlier gates.

## Gate Results

- Active roster gate: `Roster Decisions Ready`
- Active draft gate: `Draft Pool Needs Data`
- Active final money gate: `Needs Data`
- V3 preview roster gate: `Roster Decisions Need Data`
- V3 preview draft gate: `Draft Pool Needs Data`
- V3 preview final money gate: `Needs Data`

## Blocker Classification

- confidence blocker: 2
- data blocker: 8
- formula blocker: 1

## Exact Next Patch List

- data blocker: Promote v3 preview through the controlled model pipeline only after source coverage, identity, and outlier artifacts are generated in the active-model schema.
- data blocker: Do not mark v3 promoted/decision-ready until matching source coverage, identity, and outlier artifacts exist for the v3 source root.
- confidence blocker: Review player receipts and patch only source, identity, or normalization bugs.
- formula blocker: Write fixture-backed formula proposal before changing weights; do not tune from rankings alone.
- confidence blocker: Review movement receipts before promoting v3 values into active decisions.
- data blocker: Import only validated raw stat columns and recompute LVE points locally.
- data blocker: Use sourced rows as confidence context only unless schema is validated.

## Files

- Summary: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_decision_recommendation_summary.json`
- Blocker classification: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_decision_blocker_classification.csv`
- Active gate rows: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_decision_active_gate_rows.csv`
- V3 preview gate rows: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_decision_v3_preview_gate_rows.csv`
