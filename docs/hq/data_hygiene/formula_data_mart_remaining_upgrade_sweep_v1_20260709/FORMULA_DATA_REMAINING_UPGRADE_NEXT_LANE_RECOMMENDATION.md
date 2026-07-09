# Formula Data Remaining Upgrade Next Lane Recommendation

## Recommended Next Single Lane

`Model v4 Red Zone Exact Receipt Regeneration Pilot V1`

## Accuracy-First Rationale

Red-zone exact receipts have the highest near-term direct formula-accuracy upside because red-zone opportunity can affect fantasy scoring beyond raw yardage/PYF. The next lane must be a gated pilot: it should first prove source/as-of safety, then regenerate review-only receipts only if that proof passes.

Age/lifecycle sidecars are easier to freeze and remain the best fallback if red-zone source/as-of proof fails, but they are not higher direct scoring value than red-zone.

## Required Stop Condition

The red-zone pilot must stop before value generation if exact historical source artifacts, decision-date safety, identity joins, missingness classification, or source/use-gate status cannot be proven.

## Explicitly Not Recommended

- Formula Gauntlet.
- 100-candidate Gauntlet.
- Champion refinement.
- Rankings integration.
- Production/model-use.
- Red-zone value generation without source/as-of proof.
