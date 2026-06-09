# Truth Set Lab v3 Ranking Audit

Status: review-only. No formula tuning, active rankings, or gates changed.

## Files

- v3 preview folder: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_lab_v3_preview_20260515T084959`
- Audit groups: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_audit_groups.csv`
- Major movement: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_audit_major_movements.csv`
- Suspicious rankings: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3\reports\truth_set_v3_audit_suspicious_rankings.csv`

## Summary

- Truth-set players: 40
- Audit group rows: 53
- Major movement rows: 12
- Suspicious rows: 56
- Production coverage rows: 35
- Usage coverage rows: 35
- Snap coverage rows: 35
- Route quarantined rows: 27

## Verdict

v3 improves evidence coverage but still has high-severity review rows.

V3 is a real improvement over v2 because native nflverse production, real rushing/receiving first downs, play-by-play usage, and snap share now enter the preview. It is still not decision-ready because route participation is quarantined, all projections lack direct first-down projections, and several players still have large v2-to-v3 movement requiring receipt review.

## Major Movement Classification

- Jalen Coker: 11.02 value, 176 ranks (native production; real first downs; derived usage; snap share; route unavailable confidence/formula pressure; projection recompute; young bridge)
- Ricky Pearsall: 10.21 value, 158 ranks (native production; real first downs; derived usage; snap share; route unavailable confidence/formula pressure; projection recompute; young bridge)
- Lamar Jackson: 10.08 value, 141 ranks (native production; real first downs; derived usage; snap share; projection recompute)
- Jahmyr Gibbs: 8.93 value, 8 ranks (native production; real first downs; derived usage; snap share; projection recompute; young bridge)
- Jake Ferguson: -8.1 value, -165 ranks (native production; real first downs; derived usage; snap share; route unavailable confidence/formula pressure; projection recompute)
- Quentin Johnston: 7.74 value, 129 ranks (native production; real first downs; derived usage; snap share; route unavailable confidence/formula pressure; projection recompute; young bridge)
- Christian McCaffrey: 7.31 value, 11 ranks (native production; real first downs; derived usage; snap share; projection recompute)
- Devin Singletary: -7.12 value, -113 ranks (native production; real first downs; derived usage; snap share; projection recompute)
- Bijan Robinson: 6.17 value, 3 ranks (native production; real first downs; derived usage; snap share; projection recompute; young bridge)
- Brock Bowers: 6.1 value, 86 ranks (native production; real first downs; derived usage; snap share; route unavailable confidence/formula pressure; projection recompute; young bridge)
- Daniel Jones: -5.35 value, -24 ranks (native production; real first downs; derived usage; snap share; projection recompute)
- Josh Allen: -3.87 value, -148 ranks (native production; real first downs; derived usage; snap share; projection recompute)

## Suspicious Ranking Worklist

- Tee Higgins: route_data_unavailable (medium)
- Lamar Jackson: large_v2_to_v3_value_movement (medium)
- CeeDee Lamb: route_data_unavailable (medium)
- Kaleb Johnson: low_confidence_or_blocking_warning (high)
- Kaleb Johnson: missing_native_production (medium)
- Kaleb Johnson: missing_derived_usage (medium)
- Quentin Johnston: route_data_unavailable (medium)
- Quentin Johnston: possible_formula_imbalance (medium)
- Xavier Worthy: route_data_unavailable (medium)
- Romeo Doubs: route_data_unavailable (medium)
- Wan'Dale Robinson: route_data_unavailable (medium)
- Jerry Jeudy: route_data_unavailable (medium)
- Brian Thomas Jr.: route_data_unavailable (medium)
- Jalen Coker: route_data_unavailable (medium)
- Jalen Coker: large_v2_to_v3_value_movement (medium)
- Jalen Coker: possible_formula_imbalance (medium)

## Recommended Next Action

Do not tune formulas from vibes. Review the large movement rows and route-gap WR/TE rows using receipts. Patch only identity, source, or normalization bugs. Formula changes should wait for a fixture-backed imbalance note.
