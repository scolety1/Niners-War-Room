# Older / Late Lifecycle Falloff Review

## Bottom Line

Older-player falloff should be preserved as a context/guardrail overlay concept, not advanced as a dedicated scoring overlay.

## Evidence Review

Older-player falloff patterns are already partially represented by multiple accepted review-only layers:

- Age/lifecycle: accepted as an additive signal and useful lifecycle context.
- Veteran role-loss / prior-production trap: accepted as mixed/context only, with VET_008 preserving a real warning signal.
- Low snap/depth warning: useful role-support caution but too risky as an automatic scoring downgrade.
- Injury/availability caveat: useful guardrail context but not an injury prediction feature.

The veteran rule-test evidence did not support a dedicated older-player scoring overlay. The older lifecycle guard had some positive rows, but false-negative creation and mixed stability blocked promotion:

- `VET_002_OLDER_LIFECYCLE_DECLINE_GUARD_025` best full-history row: net miss reduction `10`, false-positive reduction `5`, false negatives created `7`, Spearman delta `-0.001`.
- `VET_012_LATE_LIFECYCLE_ROLE_LOSS_GUARD_050` best full-history row: net miss reduction `10`, false-positive reduction `5`, false negatives created `6`, Spearman delta `+0.002`.

## Answers

- Are older-player falloff patterns already captured by age/lifecycle? Partly yes.
- Are they captured by veteran role-loss? Partly yes, especially prior-production traps and veteran high-volume decline.
- Are they captured by low snap/depth warnings? Partly yes, as role-support caution.
- Are they captured by injury/availability caveats? Partly yes, when decline overlaps availability risk.
- Is there enough evidence for a dedicated older-player decline overlay? No, not as a scoring overlay.
- Should older-player decline stay as context/guardrail only? Yes.

## Decision

Older-player falloff should be preserved as `CONTEXT_GUARDRAIL_OVERLAY`. It is not discarded, but it should not become primary scoring, ranking simulation input, production/model-use, or hidden recommendation logic.
