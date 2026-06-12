# Build Sprint 4K: Internal Benchmark Governance

Status: governance freeze created.

Sprint 4K approves the Sprint 4J supplemented benchmark as the official internal v0 reference only. It does not approve calibrated model training, app-facing probabilities, player-facing probabilities, rankings, production deployment, or prediction-time use of label supplement sources.

## Official Internal Benchmark Policy

Benchmark policy ID:

`nwr_v0_internal_benchmark_policy_20260611`

Component policy ID:

`truth_set_v0_component_supplemented_internal_v1`

Scope:

`limited_truth_set_v0`

Policy flags:

| Policy Field | Value |
| --- | --- |
| internal only | true |
| app display allowed | false |
| calibrated probability use allowed | false |
| ranking use allowed | false |
| production deployment allowed | false |
| prediction-time supplement feature use allowed | false |

## What Is Approved

The Sprint 4J supplemented collapsed benchmark is approved as the official internal v0 reference.

Approved use:

- internal benchmark comparison
- governance/audit reference
- local research context
- future Sprint 5A feasibility planning, if it remains local/internal and does not emit player-facing probabilities

The approved component policy includes the Sprint 4H and Sprint 4I label-layer supplements:

- `player_stats.csv` for quarantined 2-point conversion and special-teams TD components
- play-by-play for strict attributed return yards, return TDs, and fumble recovery TDs

These supplements remain label-layer reconstruction sources only.

## Governance Checklist

| Check | Status | Notes |
| --- | --- | --- |
| source manifest approved for internal benchmark | pass | Canonical truth-set and supplement sources are approved for internal benchmark reference only. |
| supplement policy approved for internal benchmark | pass | `truth_set_v0_component_supplemented_internal_v1` |
| component waiver reduced internally | pass | Rare components are included for the internal supplemented reference. |
| app-facing path blocked | pass | App display allowed is false. |
| calibrated model path blocked | pass | Calibrated probability use allowed is false. |
| player-facing output blocked | pass | Public/player-facing probability output remains blocked. |
| local exports only | pass | Governance exports are local-only. |
| no public-market inputs | pass | ADP, market, consensus, rankings, projections, and trade calculators remain excluded. |
| no imported fantasy totals as labels | pass | Labels remain reconstructed from raw components. |
| prediction-feature use of supplements blocked | pass | Supplement sources are not prediction-time feature sources. |

## Blocked-Use Registry

The internal benchmark is explicitly blocked from:

- app outcome columns
- player card percentages
- public-facing probability display
- player-facing probability display
- rank sorting
- trade/decision board automation
- calibrated model release
- training-row feature inputs
- production deployment

Any override requires separate HQ approval, a final leakage audit, and the appropriate app/display/model gate.

## Future-Unblock Registry

Sprint 5 production/calibrated modeling remains blocked until the following are resolved or formally scoped out:

- broader legal historical rows beyond the limited truth-set universe
- age/DOB source registration if age buckets are desired
- next-year outcome support restored or explicitly excluded
- out-of-time validation plan
- calibration split registry
- confidence gate
- app display gate
- final leakage audit
- component policy review confirming whether the supplemented policy replaces the waiver policy as the benchmark reference

## Local Governance Exports

Sprint 4K writes local-only governance exports under:

`local_exports/outcome_probability/sprint_4k_internal_benchmark_governance/`

Expected files:

- `internal_benchmark_policy.csv`
- `blocked_use_registry.csv`
- `future_unblock_registry.csv`
- `governance_checklist.csv`
- `README_SPRINT_4K.md`

These exports are not app outputs, not model outputs, not probabilities, and not rankings.

## Sprint 5 Status

Sprint 5 production/calibrated modeling remains blocked.

A later Sprint 5A internal calibration feasibility study is allowed only if it stays local/internal, uses the Sprint 4K benchmark as a reference rather than app output, and continues to block app-facing probabilities, player-facing probabilities, rankings, push, and deployment.
